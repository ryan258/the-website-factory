import fs from 'node:fs/promises';
import path from 'node:path';
import lighthouse from 'lighthouse';
import * as chromeLauncher from 'chrome-launcher';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {ROOT, paths}=require('./qa-paths.cjs');
const routes=paths('AUDIT_PATHS');
const base=process.argv[2] || 'http://127.0.0.1:1313/';
const chrome=await chromeLauncher.launch({chromeFlags:['--headless'],chromePath:process.env.CHROME_PATH});
const output=path.join(ROOT,'reports/lighthouse');
await fs.mkdir(output,{recursive:true});
let failed=false;
try {
  for(const route of routes) {
    const result=await lighthouse(new URL(route.slice(1),base.endsWith('/')?base:base+'/').href,{port:chrome.port,output:['html','json'],onlyCategories:['performance','accessibility'],formFactor:'mobile'});
    if(!result || result.lhr.runtimeError) throw new Error(result?.lhr.runtimeError?.message || 'Lighthouse produced no report');
    const name=route.replaceAll('/','_') || 'home';
    await fs.writeFile(path.join(output,`${name}.html`),result.report[0]);
    await fs.writeFile(path.join(output,`${name}.json`),result.report[1]);
    const l=result.lhr;
    const values=[l.categories.performance.score,l.categories.accessibility.score,l.audits['largest-contentful-paint'].numericValue,l.audits['cumulative-layout-shift'].numericValue];
    const [p,a,lcp,cls]=values;
    const budgetOK=values.every(v=>typeof v==='number' && Number.isFinite(v)) && p>=.95 && a===1 && lcp<1500 && cls<.05;
    const requests=l.audits['network-requests'].details.items.length;
    const bytes=l.audits['total-byte-weight'].numericValue;
    const homeOK=route!=='/' || (Number.isFinite(bytes) && bytes<150000 && requests<=10);
    if(!budgetOK || !homeOK) failed=true;
    console.log(`${route}: performance ${p*100}, accessibility ${a*100}, LCP ${Math.round(lcp)} ms, CLS ${cls}, ${requests} requests, ${bytes} bytes${budgetOK&&homeOK?'':' — FAIL'}`);
  }
} finally { await chrome.kill(); }
process.exitCode=failed?1:0;
