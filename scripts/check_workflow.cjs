/* Bounded workflow regression: isolated browser storage, persistence, recovery, and a11y. */
const {chromium}=require('playwright');
const {AxeBuilder}=require('@axe-core/playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {ROOT,launchOptions,preview}=require('./qa-paths.cjs');
const KEY='website-factory-projects-v1';
(async()=>{
 let site;let browser;const results=[];
 try{
 site=await preview('public-workshop');
 browser=await chromium.launch(launchOptions());const context=await browser.newContext();const page=await context.newPage();const url=site.base+'site-kit/';
 const errors=[];page.on('pageerror',e=>errors.push(e.message));await page.goto(url);
 await page.locator('.wf-start-blank summary').click();
 await page.getByLabel('New project name',{exact:true}).fill('Regression fixture');await page.getByRole('button',{name:'Start project',exact:true}).click();
 await page.getByLabel('What does the business do?',{exact:true}).fill('Example service');await page.getByRole('button',{name:'2. Page plan',exact:true}).click();
 await page.getByLabel('Purpose: what does this page help the visitor do?',{exact:true}).fill('Understand the service');await page.getByRole('button',{name:'Shape this page',exact:true}).click();
 await page.getByLabel('Main page heading',{exact:true}).fill('<img src=x onerror=alert(1)>');await page.getByLabel('Section copy',{exact:true}).fill('Persistent copy');
 await page.getByLabel('Section to add',{exact:true}).selectOption('Services');await page.getByRole('button',{name:'Add section',exact:true}).click();
 await page.getByRole('button',{name:'Move Services section 2 up',exact:true}).click();
 assert.match(await page.locator('.wf-wire').first().innerText(),/Services/);assert.match(await page.evaluate(()=>document.activeElement.textContent),/Section options/);
 await page.getByRole('button',{name:'Undo',exact:true}).click();assert.match(await page.locator('.wf-wire').first().innerText(),/Introduction/);
 await page.reload();await page.getByRole('button',{name:'Open project',exact:true}).click();assert.equal(await page.getByLabel('Main page heading',{exact:true}).inputValue(),'<img src=x onerror=alert(1)>');assert.equal(await page.locator('.wf-wire img').count(),0);assert.equal(await page.locator('.wf-wire').count(),2);await page.getByLabel('Section copy',{exact:true}).first().fill('Changed after resume');assert.equal(await page.getByRole('button',{name:'Undo',exact:true}).isEnabled(),true);await page.getByRole('button',{name:'Undo',exact:true}).click();assert.equal(await page.getByLabel('Section copy',{exact:true}).first().inputValue(),'Persistent copy');results.push('Reload resumes the page editor; copy and section order persist; undo and HTML escaping work.');
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export backup',exact:true}).click();const download=await downloadPromise;const backup=fs.readFileSync(await download.path());assert.equal(JSON.parse(backup).projects.length,1);
 await page.getByRole('button',{name:'All projects',exact:true}).click();await page.locator('#import-project').setInputFiles({name:'backup.json',mimeType:'application/json',buffer:backup});assert.equal(await page.getByLabel('Project name',{exact:true}).inputValue(),'Regression fixture (imported)');
 await page.getByRole('button',{name:'All projects',exact:true}).click();const before=await page.evaluate(key=>localStorage.getItem(key),KEY);await page.locator('#import-project').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{"version":1,"projects":[{}]}')});await page.waitForFunction(()=>document.querySelector('#wf-status').textContent.includes('Import failed'));assert.match(await page.locator('#wf-status').innerText(),/Import failed/);assert.equal(await page.evaluate(key=>localStorage.getItem(key),KEY),before);results.push('Downloaded backup imports as a separate project; malformed imports leave saved data unchanged.');
 // A backup the app writes must import, and work must stop before it cannot.
 await page.locator('.wf-start-blank summary').click();
 await page.getByLabel('New project name',{exact:true}).fill('Capacity fixture');await page.getByRole('button',{name:'Start project',exact:true}).click();
 const filled=await page.evaluate(async()=>{
  const sleep=()=>new Promise(r=>setTimeout(r,0));
  const refusal=()=>{const text=document.querySelector('#wf-status').textContent;return text.includes('undone')?text:'';};
  const click=async selector=>{const el=document.querySelector(selector);if(el){el.click();await sleep();}return !!el;};
  const stage=n=>click(`[data-action="step"][data-step="${n}"]`);
  const paragraph='R\u00e9\u00e9valuation des priorit\u00e9s \u2014 '.repeat(500).slice(0,11990); // multibyte, at the field limit
  let refused='';
  for(let p=0;p<5&&!refused;p++){
   if(p){await stage(1);await click('[data-action="add-page"]');}
   await stage(2);
   for(let i=0;i<29&&!refused;i++){await click('[data-action="add-section"]');refused=refusal();}
   for(const field of document.querySelectorAll('[data-copy="body"]')){
    if(field.value)continue;
    field.value=paragraph;field.dispatchEvent(new Event('input',{bubbles:true}));await sleep();
    refused=refusal();if(refused)break;
   }
  }
  return refused;
 });
 assert.match(filled,/backup limit/,'editing past the backup limit must be refused and undone');
 const near=page.waitForEvent('download');await page.getByRole('button',{name:'Export backup',exact:true}).click();const large=fs.readFileSync(await (await near).path());
 assert.ok(large.length>500000,`capacity fixture should be a large backup, got ${large.length} bytes`);
 assert.ok(large.length<=2000000,`the app must not write a backup it refuses to read: ${large.length} bytes`);
 await page.getByRole('button',{name:'All projects',exact:true}).click();await page.locator('#import-project').setInputFiles({name:'large.json',mimeType:'application/json',buffer:large});
 await page.waitForFunction(()=>!document.querySelector('#wf-status').textContent.includes('Import failed'));
 assert.match(await page.getByLabel('Project name',{exact:true}).inputValue(),/\(imported\)$/);
 results.push(`A ${large.length}-byte backup with multibyte copy round-trips; oversized edits are refused (status: ${filled.slice(0,40)}).`);
 await page.getByRole('button',{name:'All projects',exact:true}).click();
 await page.getByRole('button',{name:'Open project',exact:true}).first().click();await page.getByRole('button',{name:'5. Design handoff',exact:true}).click();assert.equal(await page.getByRole('button',{name:'Mark plan ready for design',exact:true}).isEnabled(),false);
 for(const name of ['1. Brief','2. Page plan','3. Shape pages','4. Review','5. Design handoff']){await page.getByRole('button',{name,exact:true}).click();const axe=await new AxeBuilder({page}).include('#workflow').withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();assert.deepEqual(axe.violations.map(x=>({id:x.id,nodes:x.nodes.map(n=>n.target)})),[],name);for(const width of [320,900,1440]){await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`${name} overflow at ${width}`);}}
 await page.emulateMedia({colorScheme:'dark'});await page.getByRole('button',{name:'3. Shape pages',exact:true}).click();const darkAxe=await new AxeBuilder({page}).include('#workflow').withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();assert.deepEqual(darkAxe.violations.map(x=>({id:x.id,nodes:x.nodes.map(n=>n.target)})),[],'Dark mode editor');await page.emulateMedia({colorScheme:'light'});
 results.push('Incomplete handoff is blocked; five workflow stages pass scoped axe checks and 320/900/1440px overflow checks.');
 await page.getByRole('button',{name:'1. Brief',exact:true}).click();for(const label of ['Who is the site for?','What should visitors be able to do?','Agreed scope and constraints','Confirmed facts and their sources'])await page.getByLabel(label,{exact:true}).fill('Explicit fictional test material');
 await page.getByRole('button',{name:'2. Page plan',exact:true}).click();await page.getByLabel('Primary visitor action',{exact:true}).fill('Contact');await page.getByRole('button',{name:'3. Shape pages',exact:true}).click();
 for(let i=0;i<2;i++){await page.locator('.wf-wire input').nth(i).fill('Reviewed fixture heading');await page.getByLabel('Section copy',{exact:true}).nth(i).fill('Reviewed fictional copy');await page.getByRole('button',{name:'Section options',exact:true}).nth(i).click();await page.getByLabel('Accessibility and image notes',{exact:true}).fill('No image or form in this test section.');await page.getByLabel('Copy state',{exact:true}).selectOption('approved');}
 await page.getByRole('button',{name:'4. Review',exact:true}).click();assert.match(await page.locator('.wf-progress').innerText(),/^0 open/);for(const checkbox of await page.locator('[data-check]').all())await checkbox.check();await page.getByRole('button',{name:'5. Design handoff',exact:true}).click();await page.getByRole('button',{name:'Mark plan ready for design',exact:true}).click();assert.match(await page.locator('#wf-stage').innerText(),/Plan marked ready/);
 await page.getByRole('button',{name:'3. Shape pages',exact:true}).click();await page.getByLabel('Section copy',{exact:true}).first().fill('Changed after review');await page.getByRole('button',{name:'4. Review',exact:true}).click();assert.equal(await page.locator('[data-check]:checked').count(),0);await page.getByRole('button',{name:'5. Design handoff',exact:true}).click();assert.equal(await page.getByRole('button',{name:'Mark plan ready for design',exact:true}).isEnabled(),false);assert.equal((await page.locator('#wf-stage').innerText()).includes('Plan marked ready'),false);results.push('Ready-for-design requires complete content and explicit review; subsequent copy edits revoke readiness and review confirmations.');
 const second=await context.newPage();await second.goto(url);await second.getByRole('button',{name:'Open project',exact:true}).first().click();await second.getByRole('button',{name:'1. Brief',exact:true}).click();await second.getByLabel('What does the business do?',{exact:true}).fill('Second tab edit');await page.waitForFunction(()=>document.querySelector('#wf-status').textContent.includes('Another tab'));const protectedValue=await second.evaluate(key=>localStorage.getItem(key),KEY);await page.getByRole('button',{name:'1. Brief',exact:true}).click();await page.getByLabel('What does the business do?',{exact:true}).fill('Stale tab edit');assert.equal(await second.evaluate(key=>localStorage.getItem(key),KEY),protectedValue);results.push('Competing tab edits cannot overwrite the newer saved version.');
 const failure=await browser.newContext();await failure.addInitScript(()=>{Storage.prototype.setItem=()=>{throw new DOMException('Quota exceeded','QuotaExceededError');};});const failed=await failure.newPage();await failed.goto(url);await failed.locator('.wf-start-blank summary').click();await failed.getByLabel('New project name',{exact:true}).fill('Unsaved fixture');await failed.getByRole('button',{name:'Start project',exact:true}).click();assert.match(await failed.locator('#wf-status').innerText(),/Save failed/);assert.equal(await failed.getByRole('button',{name:'Export backup',exact:true}).isEnabled(),true);results.push('Storage failure is visible and backup export remains available.');
 assert.deepEqual(errors,[]);fs.mkdirSync(path.join(ROOT,'reports'),{recursive:true});fs.writeFileSync(path.join(ROOT,'reports/workflow-checks.json'),JSON.stringify({status:'passed',results},null,2));console.log(`Workflow checks passed: ${results.length} behavior groups; isolated fixtures only.`);
 }finally{if(browser)await browser.close().catch(()=>{});if(site)await site.close().catch(()=>{})}
})().catch(e=>{console.error(e);process.exitCode=1;});
