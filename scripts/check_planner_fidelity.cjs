/* Targeted browser -> actual backup -> compiler fidelity. Uses isolated local storage. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {spawnSync}=require('node:child_process');
const {chromium}=require('playwright');
const {AxeBuilder}=require('@axe-core/playwright');
const {ROOT,launchOptions,preview}=require('./qa-paths.cjs');
const KEY='website-factory-projects-v1';
(async()=>{
 let site,browser,scratch;
 try{
  site=await preview('public-workshop');browser=await chromium.launch(launchOptions());
  scratch=fs.mkdtempSync(path.join(os.tmpdir(),'planner-fidelity-'));
  const context=await browser.newContext(),page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));await page.goto(site.base+'site-kit/');
  const source=await page.locator('#workflow-starters').evaluate(el=>Object.fromEntries(Object.entries(JSON.parse(el.textContent)).map(([k,v])=>[k,JSON.parse(v)])));
  const download=async()=>{const pending=page.waitForEvent('download');await page.getByRole('button',{name:'Export backup',exact:true}).click();return fs.readFileSync(await (await pending).path());};
  const compile=buffer=>{
   const file=path.join(scratch,'plan.json');fs.writeFileSync(file,buffer);
   const result=spawnSync('python3',[path.join(ROOT,'scripts/from_plan.py'),file],{encoding:'utf8'});
   assert.equal(result.status,0,result.stderr);return JSON.parse(result.stdout);
  };
  for(const [slug,original] of Object.entries(source)){
   await page.locator('#starter-preset').selectOption(slug);await page.locator('[data-action=start-starter]').click();
   const buffer=await download(),project=JSON.parse(buffer).projects[0],compiled=compile(buffer);
   assert.deepEqual(project.pages.map(p=>p.slug),Object.keys(original.pages),`${slug}: starter page order`);
   assert.deepEqual(Object.keys(compiled.pages),Object.keys(original.pages),`${slug}: compiled page order`);
   for(const key of ['label','tone','palette','font_pairing'])assert.equal(compiled[key],original[key],`${slug}: ${key}`);
   for(const [key,definition] of Object.entries(original.pages)){
    assert.equal(compiled.pages[key].description,definition.description,`${slug}/${key}: description`);
    assert.equal(compiled.pages[key].sections.length,definition.sections.length);
    definition.sections.forEach((spec,i)=>assert.deepEqual(compiled.sections[compiled.pages[key].sections[i].content],original.sections[spec.content],`${slug}/${key}/${spec.content}`));
   }
   if(slug==='construction'){
    const home=project.pages.find(p=>p.slug==='home');await page.locator(`[data-action=page][data-id="${home.id}"]`).click();
    const hero=home.sections[0];
    await page.locator(`#f-body-${hero.id}`).fill('Owner revised introduction.');
    await page.locator(`[data-action=section][data-id="${hero.id}"]`).click();
    await page.getByText('AI copy assistance',{exact:true}).click();
    await page.locator('#proposal').fill('Reviewed proposal introduction.');await page.locator('[data-action=apply-proposal]').click();
    assert.equal(await page.locator(`#f-body-${hero.id}`).inputValue(),'Reviewed proposal introduction.');
    await page.locator('[data-action=undo]').click();assert.equal(await page.locator(`#f-body-${hero.id}`).inputValue(),'Owner revised introduction.');
    const itemSection=home.sections.find(s=>s.content.items?.length);
    const item=page.locator(`[data-content][data-id="${itemSection.id}"]`).filter({visible:true});
    const textField=page.locator(`[data-content='["items","0","text"]'][data-id="${itemSection.id}"]`);
    assert.ok(await item.count());await textField.fill('Owner revised item, with its title unchanged.');
    await textField.fill('');await page.locator('[data-action=step][data-step="3"]').click();
    assert.ok((await page.locator('#wf-stage').innerText()).includes(`${home.name} / ${itemSection.kind} has missing copy.`));
    await page.locator('[data-action=undo]').click();await page.locator('[data-action=step][data-step="2"]').click();
    assert.equal(await textField.inputValue(),'Owner revised item, with its title unchanged.');
    const secondary=page.locator(`[data-content='["secondary","url"]'][data-id="${hero.id}"]`);
    await secondary.fill('/contact/');
    const modified=await download(),result=compile(modified),homeResult=result.pages.home.sections;
    assert.equal(result.sections[homeResult[0].content].intro,'Owner revised introduction.');
    assert.equal(result.sections[homeResult[0].content].secondary.url,'/contact/');
    assert.equal(result.sections[homeResult[home.sections.indexOf(itemSection)].content].items[0].text,'Owner revised item, with its title unchanged.');
    await page.reload();await page.getByRole('button',{name:'Open project',exact:true}).last().click();
    assert.equal(await textField.inputValue(),'Owner revised item, with its title unchanged.');
    await page.locator('[data-action=home]').click();
    await page.locator('#import-project').setInputFiles({name:'fidelity.json',mimeType:'application/json',buffer:modified});
    const reimport=compile(await download());assert.deepEqual(reimport.sections,result.sections,'export/import must preserve the edited structure');
    await page.locator('[data-action=step][data-step="2"]').click();
    const stored=await page.evaluate(key=>JSON.parse(localStorage.getItem(key)).projects.at(-1),KEY);
    await page.locator(`[data-action=page][data-id="${stored.pages.find(p=>p.slug==='home').id}"]`).click();
    for(const width of [320,1440]){await page.setViewportSize({width,height:900});assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false,`editor overflow at ${width}`);}
    const axe=await new AxeBuilder({page}).include('#workflow').withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
    assert.deepEqual(axe.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})),[]);
    await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(os.tmpdir(),'planner-fidelity-editor.png')});
   }
   await page.locator('[data-action=home]').click();
  }
  assert.deepEqual(errors,[]);
  await page.goto(site.base+'site-kit/construction/');
  const fonts=await page.evaluate(async()=>{await document.fonts.load('700 24px "Source Serif 4"');return {loaded:document.fonts.check('700 24px "Source Serif 4"'),heading:getComputedStyle(document.querySelector('.composition h1')).fontFamily};});
  assert.equal(fonts.loaded,true);assert.match(fonts.heading,/Source Serif 4/);
  console.log(`Planner fidelity passed: ${Object.keys(source).length} complete starter exports; edited item, paragraph, proposal/undo, secondary action, missing-copy review, reload, import, scoped axe, responsive checks, and preview font loading.`);
 }finally{
  if(browser)await browser.close().catch(()=>{});if(site)await site.close().catch(()=>{});
  if(scratch)fs.rmSync(scratch,{recursive:true,force:true});
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
