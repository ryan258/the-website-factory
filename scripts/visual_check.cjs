/* Visual regression: screenshot each page and compare with saved baselines.

   node scripts/visual_check.cjs --update   # record baselines from the current build
   node scripts/visual_check.cjs            # compare; exit 1 if a page changed
   node scripts/visual_check.cjs --self-test  # check the PNG compare code, no browser

   Build first (python3 scripts/build.py). Pages come from the build, or VISUAL_PATHS
   (a JSON array). Screenshots are full-page, light mode, at 390 and 1200 px wide, with
   animations off. Baselines, current shots, and diff images live in the ignored
   reports/visual/ folder: they depend on this machine's browser and fonts, so record and
   compare on the same machine (this is a local check, not a CI gate). A page fails when
   its size changes or more than VISUAL_THRESHOLD (default 0.002 = 0.2%) of its pixels
   differ; the diff image marks changed pixels in red. */
const fs = require('node:fs');
const path = require('node:path');
const zlib = require('node:zlib');
const {ROOT, paths, launchOptions, preview} = require('./qa-paths.cjs');

// --- PNG (8-bit RGB/RGBA, not interlaced: what browsers write) -----------------------
const CRC = new Int32Array(256).map((_, n) => { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1; return c; });
const crc32 = bytes => { let c = -1; for (const b of bytes) c = CRC[(c ^ b) & 255] ^ (c >>> 8); return (c ^ -1) >>> 0; };

function decodePNG(buffer) {
  if (buffer.readUInt32BE(0) !== 0x89504e47) throw new Error('not a PNG');
  let offset = 8, width, height, type, depth, interlace;
  const data = [];
  while (offset < buffer.length) {
    const length = buffer.readUInt32BE(offset), name = buffer.toString('ascii', offset + 4, offset + 8);
    const body = buffer.subarray(offset + 8, offset + 8 + length);
    if (name === 'IHDR') [width, height, depth, type, interlace] = [body.readUInt32BE(0), body.readUInt32BE(4), body[8], body[9], body[12]];
    if (name === 'IDAT') data.push(body);
    if (name === 'IEND') break;
    offset += 12 + length;
  }
  if (depth !== 8 || interlace || ![2, 6].includes(type)) throw new Error(`unsupported PNG (depth ${depth}, type ${type}, interlace ${interlace})`);
  const channels = type === 6 ? 4 : 3, stride = width * channels;
  const raw = zlib.inflateSync(Buffer.concat(data));
  const pixels = Buffer.alloc(width * height * 4);
  let previous = Buffer.alloc(stride);
  for (let y = 0; y < height; y++) {
    const filter = raw[y * (stride + 1)];
    const line = Buffer.from(raw.subarray(y * (stride + 1) + 1, (y + 1) * (stride + 1)));
    for (let x = 0; x < stride; x++) {
      const a = x >= channels ? line[x - channels] : 0, b = previous[x], c = x >= channels ? previous[x - channels] : 0;
      const p = a + b - c, pa = Math.abs(p - a), pb = Math.abs(p - b), pc = Math.abs(p - c);
      const add = [0, a, b, (a + b) >> 1, pa <= pb && pa <= pc ? a : pb <= pc ? b : c][filter];
      if (add === undefined) throw new Error(`bad PNG filter ${filter}`);
      line[x] = (line[x] + add) & 255;
    }
    for (let x = 0; x < width; x++) {
      line.copy(pixels, (y * width + x) * 4, x * channels, x * channels + 3);
      pixels[(y * width + x) * 4 + 3] = channels === 4 ? line[x * 4 + 3] : 255;
    }
    previous = line;
  }
  return {width, height, pixels};
}

function encodePNG({width, height, pixels}) {
  const raw = Buffer.alloc(height * (width * 4 + 1));
  for (let y = 0; y < height; y++) pixels.copy(raw, y * (width * 4 + 1) + 1, y * width * 4, (y + 1) * width * 4);
  const chunk = (name, body) => {
    const head = Buffer.alloc(8); head.writeUInt32BE(body.length); head.write(name, 4, 'ascii');
    const tail = Buffer.alloc(4); tail.writeUInt32BE(crc32(Buffer.concat([head.subarray(4), body])));
    return Buffer.concat([head, body, tail]);
  };
  const ihdr = Buffer.alloc(13); ihdr.writeUInt32BE(width); ihdr.writeUInt32BE(height, 4); ihdr[8] = 8; ihdr[9] = 6;
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(raw)), chunk('IEND', Buffer.alloc(0))]);
}

/* Compare two decoded images. A pixel counts as changed when any channel moves by more than
   `tolerance`, which absorbs anti-aliasing noise. Returns {changed, ratio, diff}. */
function compare(before, after, tolerance = 24) {
  if (before.width !== after.width || before.height !== after.height) return {sizeChanged: true};
  const diff = Buffer.alloc(before.pixels.length);
  let changed = 0;
  for (let i = 0; i < before.pixels.length; i += 4) {
    const moved = [0, 1, 2, 3].some(k => Math.abs(before.pixels[i + k] - after.pixels[i + k]) > tolerance);
    if (moved) { changed++; diff.set([255, 0, 0, 255], i); }
    else { const grey = 255 - ((255 - before.pixels[i]) >> 2); diff.set([grey, grey, grey, 255], i); }
  }
  return {changed, ratio: changed / (before.width * before.height), diff: {width: before.width, height: before.height, pixels: diff}};
}

function selfTest() {
  const assert = require('node:assert/strict');
  const image = (w, h, fill) => ({width: w, height: h, pixels: Buffer.alloc(w * h * 4).map((_, i) => fill(Math.floor(i / 4) % w, Math.floor(i / 4 / w), i % 4))});
  const a = image(40, 30, (x, y, c) => c === 3 ? 255 : (x * 5 + y * 3 + c * 40) & 255);
  const round = decodePNG(encodePNG(a));
  assert.deepEqual(round.pixels, a.pixels, 'encode/decode round trip');
  const b = decodePNG(encodePNG(a));
  for (let x = 0; x < 10; x++) b.pixels.set([0, 0, 0, 255], (5 * 40 + x) * 4);
  const result = compare(a, b);
  assert.equal(result.changed, 10);
  assert.equal(compare(a, image(41, 30, () => 0)).sizeChanged, true);
  assert.equal(compare(a, round).changed, 0);
  // A real PNG written by another encoder exercises every scanline filter type in use.
  const real = decodePNG(fs.readFileSync(path.join(ROOT, 'assets/images/social-base.png')));
  assert.equal(real.pixels.length, real.width * real.height * 4);
  assert.equal(compare(real, decodePNG(encodePNG(real))).changed, 0);
  console.log('Visual check self-test passed: PNG round trip, pixel diff, size change, real image decode.');
}

async function run() {
  const {chromium} = require('playwright');
  const update = process.argv.includes('--update');
  const threshold = Number(process.env.VISUAL_THRESHOLD || 0.002);
  const dirs = Object.fromEntries(['baseline', 'current', 'diff'].map(d => [d, path.join(ROOT, 'reports/visual', d)]));
  for (const dir of Object.values(dirs)) fs.mkdirSync(dir, {recursive: true});
  // Diff images describe this run only; stale ones would point at problems already fixed.
  for (const old of fs.readdirSync(dirs.diff)) fs.unlinkSync(path.join(dirs.diff, old));
  const routes = paths('VISUAL_PATHS');
  let site;
  let browser;
  const failures = [];
  let recorded = 0, compared = 0;
  try {
    site = await preview('public');
    browser = await chromium.launch(launchOptions());
    const page = await browser.newPage();
    await page.emulateMedia({colorScheme: 'light', reducedMotion: 'reduce'});
    for (const route of routes) {
      for (const width of [390, 1200]) {
        await page.setViewportSize({width, height: 900});
        await page.goto(new URL(route.slice(1), site.base).href);
        await page.evaluate(() => document.fonts.ready);
        const name = `${(route.replace(/^\/|\/$/g, '') || 'home').replace(/\//g, '--')}@${width}.png`;
        const shot = await page.screenshot({fullPage: true, animations: 'disabled', caret: 'hide'});
        fs.writeFileSync(path.join(dirs.current, name), shot);
        const saved = path.join(dirs.baseline, name);
        if (update) { fs.writeFileSync(saved, shot); recorded++; continue; }
        if (!fs.existsSync(saved)) { failures.push(`${name}: no baseline; run with --update first`); continue; }
        const result = compare(decodePNG(fs.readFileSync(saved)), decodePNG(shot));
        compared++;
        if (result.sizeChanged) failures.push(`${name}: page size changed`);
        else if (result.ratio > threshold) {
          fs.writeFileSync(path.join(dirs.diff, name), encodePNG(result.diff));
          failures.push(`${name}: ${(result.ratio * 100).toFixed(2)}% of pixels changed (see reports/visual/diff/${name})`);
        }
      }
    }
  } finally {
    if (browser) await browser.close().catch(() => {});
    if (site) await site.close().catch(() => {});
  }
  if (update) { console.log(`Recorded ${recorded} baseline screenshot(s) in reports/visual/baseline/.`); return; }
  if (failures.length) { console.error(failures.join('\n')); process.exitCode = 1; return; }
  console.log(`Visual check passed: ${compared} screenshot(s) match their baselines.`);
}

if (require.main === module) {
  if (process.argv.includes('--self-test')) selfTest();
  else run().catch(error => { console.error(error.message); process.exitCode = 1; });
}
module.exports = {decodePNG, encodePNG, compare};
