/* Focused checks for practical components and their planning-workspace integration. */
const {chromium}=require('playwright');
const {AxeBuilder}=require('@axe-core/playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {ROOT,launchOptions,preview}=require('./qa-paths.cjs');
const registry=JSON.parse(fs.readFileSync(path.join(ROOT,'data/modules.json')));
const additions=['fit','inclusions','preparation','hours','visit','menu','events','policies','glossary','support'];
(async()=>{
 const site=await preview('public-workshop');let browser;
 try{
 browser=await chromium.launch(launchOptions());const context=await browser.newContext();const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));const base=site.base.slice(0,-1);
 await page.goto(base+'/site-kit/catalog/');
 for(const id of additions){await page.locator(`#catalog-${id}>summary`).click();for(const variant of registry[id].variants){assert.equal(await page.locator(`#example-${id}-${variant}`).isVisible(),true);assert.match(await page.locator(`#example-${id}-${variant}`).innerText(),/Illustrative content/);}}
 for(const mode of ['light','dark']){await page.emulateMedia({colorScheme:mode});const axe=new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']);for(const id of additions)axe.include(`#catalog-${id}`);const result=await axe.analyze();assert.deepEqual(result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],mode);for(const width of [320,900,1440]){await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,mode+' '+width);}}
 const nojs=await browser.newContext({javaScriptEnabled:false});const plain=await nojs.newPage();await plain.goto(base+'/site-kit/catalog/');await plain.locator('#catalog-policies>summary').focus();await plain.keyboard.press('Enter');await plain.locator('#example-policies-accordion summary').first().focus();await plain.keyboard.press('Enter');assert.equal(await plain.locator('#example-policies-accordion details').first().getAttribute('open'),'');
 await page.goto(base+'/site-kit/');await page.getByLabel('New project name',{exact:true}).fill('Component regression fixture');await page.getByRole('button',{name:'Start project',exact:true}).click();await page.getByRole('button',{name:'3. Shape pages',exact:true}).click();assert.equal(await page.locator('#section-kind option').count(),Object.keys(registry).length);
 for(const id of additions){await page.getByLabel('Section to add',{exact:true}).selectOption(registry[id].name);assert.match(await page.locator('#section-guidance').innerText(),new RegExp(registry[id].purpose.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));await page.getByRole('button',{name:'Add section',exact:true}).click();assert.equal(await page.locator('.wf-inspector').getByText(registry[id].copy_guidance,{exact:false}).count(),1);}
 assert.equal(await page.locator('.wf-wire').count(),11);await page.reload();await page.getByRole('button',{name:'Open project',exact:true}).click();assert.equal(await page.locator('.wf-wire').count(),11);const axe=await new AxeBuilder({page}).include('#workflow').withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();assert.deepEqual(axe.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[]);assert.deepEqual(errors,[]);
 fs.mkdirSync(path.join(ROOT,'reports'),{recursive:true});fs.writeFileSync(path.join(ROOT,'reports/component-expansion.json'),JSON.stringify({status:'passed',families:additions,variants:20,catalogThemes:['light','dark'],widths:[320,900,1440],keyboardWithoutJS:true,plannerChoices:Object.keys(registry).length,plannerPersistence:true},null,2));console.log('Component checks passed: 10 new families / 20 variants, two themes, three widths, no-JS keyboard disclosures, 30 planner choices and saved selection round trip.');
 }finally{if(browser)await browser.close();await site.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
