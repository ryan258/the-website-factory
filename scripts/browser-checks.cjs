const {chromium} = require('playwright');
const {AxeBuilder} = require('@axe-core/playwright');
const fs = require('node:fs');
const path = require('node:path');
const {ROOT, paths} = require('./qa-paths.cjs');
(async () => {
  const routes = paths('CHECK_PATHS');
  const base = process.env.PREVIEW_URL || 'http://127.0.0.1:1313/';
  const browser = await chromium.launch({headless:true, ...(process.env.CHROME_PATH ? {executablePath:process.env.CHROME_PATH} : {})});
  const results = [];
  const failures = [];
  const reportDir = path.join(ROOT, 'reports');
  fs.mkdirSync(reportDir, {recursive:true});
  fs.writeFileSync(path.join(reportDir,'browser-checks.json'), JSON.stringify({status:'running'}));
  try {
    const context = await browser.newContext();
    const page = await context.newPage();
    for (const route of routes) {
      for (const mode of ['light', 'dark']) {
        await page.emulateMedia({colorScheme:mode});
        await page.setViewportSize({width:1200,height:900});
        const url = new URL(route.slice(1), base.endsWith('/') ? base : base + '/');
        const response = await page.goto(url.href);
        if (!response || response.status() !== 200) throw new Error(`${url}: expected HTTP 200`);
        await page.evaluate(() => document.fonts.ready);
        const axe = await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
        const h1 = await page.locator('h1').count();
        const noindex = await page.locator('meta[name="robots"]').evaluateAll(nodes => nodes[0]?.getAttribute('content') ?? null);
        const widths = [];
        for (const width of [320,600,900,1200]) {
          await page.setViewportSize({width,height:900});
          widths.push({width,overflow:await page.evaluate(() => document.documentElement.scrollWidth > innerWidth)});
        }
        const result = {route,mode,h1,noindex,violations:axe.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),widths};
        results.push(result);
        if (h1 !== 1 || noindex !== 'noindex' || axe.violations.length || widths.some(w=>w.overflow)) failures.push(`${route} (${mode})`);
      }
    }
    fs.writeFileSync(path.join(reportDir,'browser-checks.json'),JSON.stringify(results,null,2));
    console.log(`${routes.length} pages, two color modes, four widths: ${failures.length ? 'FAILED '+failures.join(', ') : 'passed'}. Report: reports/browser-checks.json`);
    process.exitCode = failures.length ? 1 : 0;
  } finally { await browser.close(); }
})().catch(error => {
  fs.mkdirSync(path.join(ROOT,'reports'),{recursive:true});
  fs.writeFileSync(path.join(ROOT,'reports/browser-checks.json'),JSON.stringify({status:'failed',error:error.message},null,2));
  console.error(error.message); process.exitCode=1;
});
