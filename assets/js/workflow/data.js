// Page-provided data and fixed limits. Hugo writes the module registry and starter presets into
// the page (layouts/_default/kit.html); everything else here is a constant.
export const app = document.querySelector('#wf-app');
export const status = document.querySelector('#wf-status');
export const KEY = 'website-factory-projects-v1';
export const steps = ['Brief', 'Page plan', 'Shape pages', 'Review', 'Design handoff'];

export const registry = JSON.parse(document.querySelector('#workflow-library').textContent);
export const starters = JSON.parse(document.querySelector('#workflow-starters').textContent);
// Each starter arrives as its original JSON text, so authored page order survives.
for (const key in starters) starters[key] = JSON.parse(starters[key]);

// Planner labels for the eight core modules; every other module uses its registry name.
// scripts/from_plan.py keeps an identical map (scripts/test_from_plan.py reads this line).
export const legacy={hero:'Introduction',services:'Services',about:'About',work:'Proof',process:'Process',faq:'FAQ',contact:'Contact',cta:'Call to action'};
export const library = Object.fromEntries(Object.entries(registry).map(([key, value]) => [legacy[key] || value.name, {...value, key}]));
export const kinds = Object.keys(library);
export const categories = [...new Set(kinds.map(k => library[k].category || 'Core sections'))];

export const checks = [
  'I followed the main visitor journey and checked that each page has a useful next step.',
  'I reviewed headings, link wording, image needs, and form labels for accessibility.',
  'I checked business claims and recorded any remaining content or design questions.',
];

// One capacity limit, enforced where work is added, so every backup this app writes is a
// backup it can also read. Measured in UTF-8 bytes on the exact exported text.
export const MAX_BACKUP = 2000000, MAX_BACKUP_LABEL = '2 MB';
// Editing stops just under the file limit: importing a backup re-labels it '(imported)',
// and that copy must stay importable too.
export const CAPACITY = MAX_BACKUP - 32;
