/* Focused checks for visible module variants, native controls, and no-JS previews. */
const {chromium}=require('playwright');
const {AxeBuilder}=require('@axe-core/playwright');
const fs=require('node:fs');
const path=require('node:path');
const ROOT=path.resolve(__dirname,'..');
const base=process.env.PREVIEW_URL||'http://127.0.0.1:14722/';
(async()=>{
 const browser=await chromium.launch({headless:true});
 const results=[];const failures=[];
 const out=path.join(ROOT,'reports');fs.mkdirSync(out,{recursive:true});
 try {
  const context=await browser.newContext();const page=await context.newPage();
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  for(const mode of ['light','dark']){
   await page.emulateMedia({colorScheme:mode});await page.setViewportSize({width:1200,height:900});
   await page.goto(base+'site-kit/');await page.evaluate(()=>document.fonts.ready);
   await page.locator('.kit-module').evaluateAll(nodes=>nodes.forEach(n=>n.open=true));
   const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
   const widths=[];
   for(const width of [320,390,600,900,1200]){
    await page.setViewportSize({width,height:900});
    widths.push({width,overflow:await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth)});
   }
   const variants=await page.locator('.kit-variant').count();
    results.push({mode,variants,violations:axe.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)})),widths});
    if(axe.violations.length||variants!==41||widths.some(w=>w.overflow))failures.push('expanded '+mode);
  }
  await page.goto(base+'site-kit/style-guide/');
  const sgAxe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa','wcag22aa']).analyze();
  if(sgAxe.violations.length)failures.push('style guide a11y: '+sgAxe.violations.map(v=>v.id).join(','));
  for(const width of [320,390,600,900,1200]){
    await page.setViewportSize({width,height:900});
    if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))failures.push(`style guide overflow at ${width}px`);
  }
  await page.setViewportSize({width:1440,height:1000});await page.emulateMedia({colorScheme:'light'});
  await page.goto(base+'site-kit/');await page.screenshot({path:path.join(out,'workshop-desktop.png'),fullPage:true});
  const summary=page.locator('#catalog-faq > summary');await summary.focus();await page.keyboard.press('Enter');
  if(!await page.locator('#catalog-faq').evaluate(e=>e.open))failures.push('keyboard catalog');
  const question=page.locator('#example-faq-accordion summary').first();await question.focus();await page.keyboard.press('Enter');
  if(!await question.evaluate(e=>e.parentElement.open))failures.push('keyboard FAQ');
  await page.setViewportSize({width:390,height:844});await page.goto(base+'site-kit/');await page.screenshot({path:path.join(out,'workshop-mobile.png'),fullPage:true});
  for(const slug of ['agency','contractor','consultant','local-service']){
   await page.setViewportSize({width:1440,height:1000});await page.goto(base+'site-kit/'+slug+'/');
   await page.screenshot({path:path.join(out,slug+'-desktop.png'),fullPage:true});
   await page.getByRole('link',{name:'Start a conversation',exact:false}).first().click();
   if(!page.url().endsWith('#preview-contact'))failures.push(slug+' contact preview');
   await page.getByRole('link',{name:'Explore our services',exact:false}).click();
   if(!page.url().includes('/site-kit/'+slug+'/#services-'))failures.push(slug+' services preview');
  }
  const nojs=await browser.newContext({javaScriptEnabled:false,viewport:{width:390,height:844}});
  const p=await nojs.newPage();await p.goto(base+'site-kit/');
  await p.locator('#catalog-services > summary').click();
  if(!await p.locator('#example-services-cards h2').isVisible())failures.push('no-JS catalog');
  await p.goto(base+'contact/');
  if(!await p.locator('button[type=submit]').isDisabled())failures.push('disabled contact');
  await p.goto(base+'contact/received/');
  if(!await p.getByText('Message delivery is disabled', {exact:false}).isVisible())failures.push('honest receipt');
  if(errors.length)failures.push(...errors);
  fs.writeFileSync(path.join(out,'workshop-checks.json'),JSON.stringify({results,failures,keyboard:'native catalog and FAQ',noJavaScript:'catalog and contact',styleGuide:'zero a11y violations'},null,2));
  console.log(`41 expanded variants, living style guide, two themes, five widths, keyboard, no-JS and preview contact paths: ${failures.length?'FAILED '+failures.join(', '):'passed'}`);
  process.exitCode=failures.length?1:0;
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
