const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const ROOT = path.resolve(__dirname, '..');
function paths(variable) {
  if (process.env[variable]) {
    const selected = JSON.parse(process.env[variable]);
    if (!Array.isArray(selected) || !selected.length || selected.some(p => typeof p !== 'string' || !/^\/(?!\/)/.test(p) || /[?#]/.test(p))) throw new Error(`${variable} must be a JSON array of local page paths`);
    return selected;
  }
  const output = path.resolve(ROOT, process.env.SITE_OUTPUT || 'public');
  const found = [];
  function visit(dir) {
    for (const entry of fs.readdirSync(dir, {withFileTypes:true})) {
      const file = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(file);
      else if (entry.isFile() && entry.name === 'index.html') found.push('/' + path.relative(output, file).split(path.sep).join('/').replace(/index\.html$/, ''));
    }
  }
  visit(output);
  if (!found.length) throw new Error('No generated pages. Run python3 scripts/build.py first.');
  return found.sort();
}

/* Browser launch options shared by every check: CHROME_PATH selects a local browser. */
function launchOptions() {
  // A browser that cannot start fails after a minute instead of hanging the whole check.
  return {headless: true, timeout: 60000, ...(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {})};
}

/* Site-wide response headers from static/_headers (the `/*` block), so local checks see the
   same Content-Security-Policy that Cloudflare Pages sends. */
function siteHeaders() {
  const headers = {};
  let global = false;
  for (const line of fs.readFileSync(path.join(ROOT, 'static/_headers'), 'utf8').split('\n')) {
    if (!line.trim()) continue;
    if (!/^\s/.test(line)) { global = line.trim() === '/*'; continue; }
    const at = line.indexOf(':');
    if (global && at > 0) headers[line.slice(0, at).trim()] = line.slice(at + 1).trim();
  }
  return headers;
}

const TYPES = {'.html':'text/html', '.js':'text/javascript', '.css':'text/css', '.json':'application/json', '.svg':'image/svg+xml',
  '.png':'image/png', '.jpg':'image/jpeg', '.webp':'image/webp', '.woff2':'font/woff2', '.xml':'application/xml', '.txt':'text/plain'};

/* Serve built output on a free loopback port, or use PREVIEW_URL when it is set.
   Resolves to {base, close}; base always ends with '/'. */
async function preview(defaultOutput) {
  if (process.env.PREVIEW_URL) {
    const base = process.env.PREVIEW_URL;
    return {base: base.endsWith('/') ? base : base + '/', close: async () => {}};
  }
  const output = path.resolve(ROOT, process.env.SITE_OUTPUT || defaultOutput);
  if (!fs.existsSync(path.join(output, 'index.html'))) throw new Error(`No build in ${output}. Run python3 scripts/build.py first.`);
  const headers = siteHeaders();
  const server = http.createServer((req, res) => {
    let name = decodeURIComponent(new URL(req.url, 'http://localhost').pathname);
    if (name.endsWith('/')) name += 'index.html';
    const file = path.resolve(output, '.' + name);
    if (!file.startsWith(output + path.sep)) { res.writeHead(403).end(); return; }
    try {
      const body = fs.readFileSync(file);
      for (const [key, value] of Object.entries(headers)) res.setHeader(key, value);
      res.setHeader('Content-Type', TYPES[path.extname(file)] || 'application/octet-stream');
      res.end(body);
    } catch { res.writeHead(404).end(); }
  });
  await new Promise((resolve, reject) => { server.once('error', reject); server.listen(0, '127.0.0.1', resolve); });
  return {base: `http://127.0.0.1:${server.address().port}/`, close: () => new Promise(resolve => server.close(resolve))};
}

/* Collect Content-Security-Policy violations, which browsers report only on the console. */
function watchCSP(page, into) {
  page.on('console', message => { if (/Content Security Policy/i.test(message.text())) into.push(`CSP: ${message.text()}`); });
}
module.exports = {ROOT, paths, launchOptions, preview, watchCSP};
