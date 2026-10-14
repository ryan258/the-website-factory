/* Targeted checks for the catalog layouts and their planning-workspace integration. */
const {chromium}=require('playwright');
const {AxeBuilder}=require('@axe-core/playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const {ROOT,launchOptions,preview}=require('./qa-paths.cjs');
const registry=JSON.parse(fs.readFileSync(path.join(ROOT,'data/modules.json')));
const examples=JSON.parse(fs.readFileSync(path.join(ROOT,'data/examples.json')));
const families=Object.keys(registry);
const legacy={hero:'Introduction',services:'Services',about:'About',work:'Proof',process:'Process',faq:'FAQ',contact:'Contact',cta:'Call to action'};
const plannerName=id=>legacy[id]||registry[id].name;
const tags=['wcag2a','wcag2aa','wcag21aa','wcag22aa'];
(async()=>{
 const site=await preview('public-workshop');let browser;
 try{
  browser=await chromium.launch(launchOptions());
  const context=await browser.newContext();
  const page=await context.newPage();const errors=[];
  page.on('pageerror',e=>errors.push(e.message));const base=site.base.slice(0,-1);
  await page.goto(base+'/site-kit/catalog/');
  for(const id of families){
   assert.equal(registry[id].variants.length,3,id+' layout count');
   await page.locator(`#catalog-${id}>summary`).click();
   for(const variant of registry[id].variants){
    const example=page.locator(`#example-${id}-${variant}`);
    assert.equal(await example.isVisible(),true,id+' '+variant);
    assert.equal(await example.locator('h2').first().innerText(),examples[id].title);
   }
  }
  assert.deepEqual(await page.evaluate(()=>{const ids=[...document.querySelectorAll('[id]')].map(x=>x.id);return ids.filter((id,i)=>ids.indexOf(id)!==i)}),[],'unique instance IDs');
  // Scope accessibility scans to the component library and exercise both arrangements.
  for(const arrangement of ['Full width','Compare layouts']){
   for(const id of families)await page.getByRole('group',{name:`${registry[id].name} preview arrangement`,exact:true}).getByLabel(arrangement,{exact:true}).check();
   for(const mode of ['light','dark']){
    await page.emulateMedia({colorScheme:mode});await page.setViewportSize({width:1440,height:900});
    const result=await new AxeBuilder({page}).include('#library').withTags(tags).analyze();
    assert.deepEqual(result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[],arrangement+' '+mode);
    for(const width of [320,900,1440]){
     await page.setViewportSize({width,height:900});
     assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,arrangement+' '+mode+' '+width);
    }
   }
  }
  for(const id of families){
   const previews=page.locator(`#catalog-${id} .kit-variant`);
   assert.equal(Math.round((await previews.nth(0).boundingBox()).y),Math.round((await previews.nth(1).boundingBox()).y),id+' comparison columns');
  }
  await page.setViewportSize({width:320,height:900});
  for(const id of families){const previews=page.locator(`#catalog-${id} .kit-variant`);assert.ok((await previews.nth(1).boundingBox()).y>(await previews.nth(0).boundingBox()).y,id+' comparison stacks');}
  // Each brief instance must validate, progress, and reset independently.
  for(const variant of registry['project-brief'].variants){
   const widget=page.locator(`#example-project-brief-${variant} [data-project-brief]`);
   await widget.getByLabel('Service area').selectOption({index:1});
   await widget.getByLabel('What would you like done?').fill('Illustrative layout check');
   await widget.getByRole('button',{name:'Next step',exact:true}).click();
   await widget.getByLabel('Town or general location').fill('Example town');
   await widget.getByLabel('Preferred timing').selectOption({index:4});
   await widget.getByRole('button',{name:'Next step',exact:true}).click();
   await widget.getByLabel('Your name').fill('Example visitor');
   await widget.getByLabel('Email address').fill('visitor@example.invalid');
   await widget.getByRole('button',{name:'Prepare brief',exact:true}).click();
   assert.match(await widget.locator('[data-brief-summary]').innerText(),/Illustrative layout check/);
   await widget.getByRole('button',{name:'Start over',exact:true}).click();
   assert.equal(await widget.getByLabel('What would you like done?').inputValue(),'');
  }
  const nojs=await browser.newContext({javaScriptEnabled:false});const plain=await nojs.newPage();
  await plain.goto(base+'/site-kit/catalog/');
  for(const id of ['fit','inclusions','policies']){
   await plain.locator(`#catalog-${id}>summary`).focus();await plain.keyboard.press('Enter');
   const variant=id==='policies'?'accordion':'disclosures';const disclosure=plain.locator(`#example-${id}-${variant} details`).first();
   await disclosure.locator('summary').focus();await plain.keyboard.press('Enter');assert.equal(await disclosure.getAttribute('open'),'');
  }
  await plain.getByRole('group',{name:'Is this right for you? preview arrangement',exact:true}).getByLabel('Full width',{exact:true}).focus();await plain.keyboard.press('ArrowRight');
  assert.equal(await plain.getByRole('group',{name:'Is this right for you? preview arrangement',exact:true}).getByLabel('Compare layouts',{exact:true}).isChecked(),true);
  await page.goto(base+'/site-kit/');await page.setViewportSize({width:1440,height:900});
  await page.locator('.wf-start-blank summary').click();await page.getByLabel('New project name',{exact:true}).fill('Component regression fixture');
  await page.getByRole('button',{name:'Start project',exact:true}).click();await page.getByRole('button',{name:'3. Shape pages',exact:true}).click();
  assert.equal(await page.locator('#section-kind option').count(),families.length);
  for(const id of families){
   await page.getByLabel('Section to add',{exact:true}).selectOption(plannerName(id));
   assert.ok((await page.locator('#section-guidance').innerText()).includes(registry[id].purpose));
   await page.getByRole('button',{name:'Add section',exact:true}).click();
   assert.equal(await page.locator('#section-variant option').count(),3);
   await page.locator('#section-variant').selectOption(registry[id].variants[2]);
  }
  assert.equal(await page.locator('.wf-wire').count(),families.length+1);
  await page.reload();await page.getByRole('button',{name:'Open project',exact:true}).click();
  assert.equal(await page.locator('.wf-wire').count(),families.length+1);
  for(const id of families)assert.equal(await page.locator('.wf-wire').filter({hasText:`${plannerName(id)} / ${registry[id].variants[2]}`}).count(),1,id+' saved layout');
  const result=await new AxeBuilder({page}).include('#workflow').withTags(tags).analyze();
  assert.deepEqual(result.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),[]);assert.deepEqual(errors,[]);
  const variants=families.reduce((n,id)=>n+registry[id].variants.length,0);
  fs.mkdirSync(path.join(ROOT,'reports'),{recursive:true});
  fs.writeFileSync(path.join(ROOT,'reports/component-expansion.json'),JSON.stringify({status:'passed',families,variants,catalogThemes:['light','dark'],widths:[320,900,1440],keyboardWithoutJS:true,uniqueInstanceIds:true,projectBriefInstances:3,plannerChoices:families.length,plannerPersistence:true,comparisonModes:['full','compare']},null,2));
  console.log(`Component checks passed: ${families.length} families / ${variants} layouts, both arrangements and themes, three widths, unique IDs, three independent brief forms, no-JS keyboard controls, saved planner layouts.`);
 }finally{if(browser)await browser.close();await site.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
