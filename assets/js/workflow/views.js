// HTML for each planner screen. Every value from a project passes through esc().
import {app, categories, checks, kinds, library, starters, steps} from './data.js';
import {bodyField, contentLabel, contentLeaves, hasBody, issues} from './model.js';
import {page, project, section, state} from './state.js';

export const esc = x => String(x ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
export const button = (text, action, extra = '') => `<button type="button" data-action="${action}" ${extra}>${esc(text)}</button>`;

function field(label, key, value, area = false, help = '', attributes = '') {
  const helpId = `wf-help-${key.replace(/[^a-z0-9_-]/gi, '-')}`;
  return `<label for="f-${esc(key)}">${esc(label)}</label>`
    + `<${area ? 'textarea' : 'input'} id="f-${esc(key)}" ${attributes || `data-field="${esc(key)}"`} ${area ? '' : 'type="text"'} maxlength="12000" aria-describedby="${helpId}"${area ? '' : ` value="${esc(value)}"`}>`
    + `${area ? esc(value) + '</textarea>' : ''}`
    + `<small class="wf-help" id="${helpId}">${esc(help)}</small>`;
}

export function guidance(kind) {
  const item = library[kind];
  const catalog = document.querySelector('#workflow').dataset.catalogUrl;
  return `<p><strong>Purpose:</strong> ${esc(item.purpose)}</p>`
    + `${item.copy_guidance ? `<p><strong>Copy:</strong> ${esc(item.copy_guidance)}</p>` : ''}`
    + `${item.a11y_guidance ? `<p><strong>Accessibility:</strong> ${esc(item.a11y_guidance)}</p>` : ''}`
    + `<p class="wf-small">${item.variants.length} reference layouts · ${item.required.map(esc).join(', ')}`
    + `${item.dependencies.length ? ' · Requires page: ' + item.dependencies.map(esc).join(', ') : ''}</p>`
    + `<a href="${esc(catalog)}#catalog-${esc(item.key)}">Inspect ${esc(kind)} layouts</a>`;
}

// One field per structured value (items, links, images); title, body and action have their own.
function contentFields(s) {
  if (!s.content) return '';
  const leaf = (path, value) => {
    const id = `detail-${s.id}-${path.join('-')}`, attrs = `data-content="${esc(JSON.stringify(path))}" data-id="${esc(s.id)}"`;
    const options = path[0] === 'items' ? (library[s.kind].item_choices || {})[path.at(-1)] : null;
    if (options) {
      return `<label for="${esc(id)}">${esc(contentLabel(path))}</label>`
        + `<select id="${esc(id)}" ${attrs}>${options.map(option => `<option ${option === value ? 'selected' : ''}>${esc(option)}</option>`).join('')}</select>`;
    }
    return field(contentLabel(path), id, value, !['url', 'image', 'imageAlt', 'title', 'label'].includes(path.at(-1)),
      path.at(-1) === 'image' ? 'Local path under assets/. Confirm the image rights.' : 'Confirm the wording and destination.', attrs);
  };
  return Object.entries(s.content).filter(([key]) => !['title', bodyField(s), 'action'].includes(key)).map(([key, value]) => {
    if (!Array.isArray(value)) return contentLeaves(value, [key]).map(([path, text]) => leaf(path, text)).join('');
    const controls = index => `data-id="${esc(s.id)}" data-array="${esc(key)}" data-index="${index}"`;
    const item = (entry, index) => `<fieldset><legend>Item ${index + 1}</legend>`
      + contentLeaves(entry, [key, String(index)]).map(([path, text]) => leaf(path, text)).join('')
      + `<div class="wf-actions">`
      + button('Move item up', 'item-up', controls(index) + (index === 0 ? ' disabled' : ''))
      + button('Move item down', 'item-down', controls(index) + (index === value.length - 1 ? ' disabled' : ''))
      + button('Remove item', 'item-remove', controls(index))
      + `</div></fieldset>`;
    return `<fieldset><legend>${esc(contentLabel([key]))}</legend>`
      + value.map(item).join('')
      + button('Add item', 'item-add', controls(value.length) + (value.length >= 40 ? ' disabled' : ''))
      + `</fieldset>`;
  }).join('');
}

function copyEditor(s, i) {
  const attrs = `data-id="${esc(s.id)}"`;
  return field(i === 0 ? 'Main page heading' : 'Section heading', `title-${s.id}`, s.title, false,
    'Write a clear heading using confirmed facts.', `data-copy="title" ${attrs}`)
    + (hasBody(s) ? field('Section copy', `body-${s.id}`, s.body, true,
      'Edit the main paragraph. Items and other content have separate fields below.', `data-copy="body" ${attrs}`) : '')
    + contentFields(s);
}

function home() {
  const card = p => `<article class="wf-box"><h3>${esc(p.name)}</h3>`
    + `<p>${p.pages.length} pages · Resume: ${esc(steps[p.view?.step] || 'Brief')} · Updated ${esc(new Date(p.updated).toLocaleString())}`
    + `${p.starterPreset ? ` · Started from ${esc(starters[p.starterPreset]?.name || p.starterPreset)}` : ''}</p>`
    + button('Open project', 'open', `data-id="${esc(p.id)}"`)
    + `</article>`;
  const projects = state.db.projects.length ? state.db.projects.map(card).join('') : '<p class="wf-empty">No saved projects yet.</p>';
  return document.querySelector('#wf-home-template').innerHTML.replace('<div id="wf-projects"></div>', projects);
}

function brief() {
  const p = project();
  return `<h2>1. Define the project</h2><p>Use confirmed information. Keep assumptions and unanswered questions in their own field.</p>`
    + `<div class="wf-two"><div>`
    + field('Project name', 'project.name', p.name, false, 'A short internal title you will recognize, such as the business name or project nickname.')
    + field('What does the business do?', 'project.business', p.business, true, 'Describe the service in plain language. Put unverified details under Unknowns.')
    + field('Who is the site for?', 'project.audience', p.audience, true, 'Describe the audience and its needs using confirmed information.')
    + field('What should visitors be able to do?', 'project.goal', p.goal, true, 'Name the main next step: a quote, booking, or finding information.')
    + `</div><div>`
    + field('Agreed scope and constraints', 'project.scope', p.scope, true, 'Record agreed inclusions, limits, and timing. Mark open decisions.')
    + field('Confirmed facts and their sources', 'project.facts', p.facts, true, 'List facts checked with the business and their sources.')
    + field('Unknowns, assumptions, and missing material', 'project.unknowns', p.unknowns, true, 'List assumptions and details still to confirm. Keep them separate from facts.')
    + `</div></div>`
    + button('Continue to page plan', 'step', 'data-step="1" class="primary"');
}

function pagesNav() {
  return `<aside class="wf-pages" aria-label="Project pages"><h3>Pages</h3>`
    + project().pages.map(pg => button(pg.name || 'Untitled page', 'page', `data-id="${esc(pg.id)}" ${pg.id === state.pageId ? 'aria-current="true"' : ''}`)).join('')
    + button('Add page', 'add-page')
    + `</aside>`;
}

function pageFields() {
  const pg = page();
  if (!pg) return '<p>Add a page to begin.</p>';
  const pages = project().pages;
  return field('Page name', 'page.name', pg.name, false, 'Use a distinct name, such as Home or Services.')
    + field('Purpose: what does this page help the visitor do?', 'page.purpose', pg.purpose, true, 'Describe the visitor need this page answers.')
    + field('Primary visitor action', 'page.action', pg.action, false, 'Name the next step, such as viewing services or requesting an estimate.')
    + `<div class="wf-actions">`
    + button('Move page up', 'page-up', pages.indexOf(pg) === 0 ? 'disabled' : '')
    + button('Move page down', 'page-down', pages.indexOf(pg) === pages.length - 1 ? 'disabled' : '')
    + button('Remove page', 'remove-page', 'class="danger"')
    + `</div>`;
}

function plan() {
  return `<h2>2. Plan the site</h2><p>Give each page a purpose before choosing its sections.</p>`
    + `<div class="wf-grid">${pagesNav()}<section class="wf-box">${pageFields()}</section>`
    + `<aside class="wf-box"><h3>Plan from the brief</h3><p><strong>Visitor goal:</strong> ${esc(project().goal) || 'Not yet defined'}</p>`
    + `<p>Start with the smallest useful site. Add pages when they answer a distinct visitor need.</p>`
    + button('Shape this page', 'step', 'data-step="2"')
    + `</aside></div>`;
}

// One section in the page wireframe: its copy editor when focused, else its heading.
function wire(x, i, pg) {
  const open = !state.compact || x.id === state.sectionId;
  return `<article class="wf-wire ${x.id === state.sectionId ? 'selected' : ''}" data-section="${esc(x.id)}">`
    + `<p class="wf-small">${i + 1}. ${esc(x.kind)}${x.variant ? ` / ${esc(x.variant)}` : ''} · ${esc(x.state)}</p>`
    + (open ? copyEditor(x, i) : `<h4>${esc(x.title || 'Untitled section')}</h4><p>Select Section options to edit this section.</p>`)
    + `${x.cta ? `<p>Action: ${esc(x.cta)} → ${esc(x.target || 'Destination needed')}</p>` : ''}`
    + `<div class="wf-actions">`
    + button('Section options', 'section', `data-id="${esc(x.id)}"`)
    + button('Move up', 'up', `data-id="${esc(x.id)}" ${i === 0 ? 'disabled' : ''} aria-label="Move ${esc(x.kind)} section ${i + 1} up"`)
    + button('Move down', 'down', `data-id="${esc(x.id)}" ${i === pg.sections.length - 1 ? 'disabled' : ''} aria-label="Move ${esc(x.kind)} section ${i + 1} down"`)
    + `</div></article>`;
}

function addSection() {
  const options = categories.map(c => `<optgroup label="${esc(c)}">`
    + kinds.filter(k => (library[k].category || 'Core sections') === c).map(k => `<option>${esc(k)}</option>`).join('')
    + `</optgroup>`).join('');
  return `<label for="section-kind">Section to add</label>`
    + `<small class="wf-help" id="section-kind-help">Choose a purpose; review its content and accessibility guidance below.</small>`
    + `<p class="wf-small">${kinds.length} component families available. Choose a purpose, then add a blank section.</p>`
    + `<select id="section-kind" aria-describedby="section-kind-help section-guidance">${options}</select>`
    + `<div id="section-guidance" class="wf-box" aria-live="polite">${guidance(kinds[0])}</div>`
    + `<p>${button('Add section', 'add-section')}</p>`;
}

function inspector(s) {
  if (!s) return '<p>Select a section to edit its options.</p>';
  const variants = library[s.kind].variants;
  return `<p>${esc(s.kind)}${s.variant ? ` / ${esc(s.variant)}` : ''}</p>${guidance(s.kind)}`
    + `<label for="section-variant">Layout</label><select id="section-variant" data-field="section.variant">`
    + variants.map(v => `<option ${v === (s.variant || variants[0]) ? 'selected' : ''}>${esc(v)}</option>`).join('')
    + `</select>`
    + `<label for="copy-state">Copy state</label><select id="copy-state" data-field="section.state" aria-describedby="copy-state-help">`
    + ['missing', 'draft', 'approved'].map(x => `<option ${s.state === x ? 'selected' : ''}>${x}</option>`).join('')
    + `</select>`
    + `<small class="wf-help" id="copy-state-help">Missing needs copy; Draft needs review; Approved has been checked. Edits return it to Draft.</small>`
    + field('Action label (optional)', 'section.cta', s.cta, false, 'Use the words for a link or button. Leave blank if this section needs no action.')
    + field('Action destination or intended next step (optional)', 'section.target', s.target, false, 'Use a local path, https://, mailto:, or tel: link. Leave blank for no action.')
    + field('Accessibility and image notes', 'section.a11y', s.a11y, true, 'Record image meaning, decorative status, alt text, and accessible link or form labels. Write “not needed” if none apply.')
    + button('Remove section', 'remove-section', 'class="danger"')
    + `<details><summary>AI copy assistance</summary>`
    + `<p class="wf-small">No AI service is connected. Use the prompt in your chosen assistant, then paste its proposal for review. Nothing is sent from this tool.</p>`
    + button('Prepare copy prompt', 'prompt')
    + `<div id="copy-prompt"></div>`
    + `<label for="proposal">Proposed section copy</label>`
    + `<textarea id="proposal" maxlength="12000" aria-describedby="proposal-help" placeholder="Paste a proposed revision">${esc(s.proposal || '')}</textarea>`
    + `<small class="wf-help" id="proposal-help">Saved separately. Check every statement against confirmed facts before applying.</small>`
    + `<p>${button('Apply proposal as draft', 'apply-proposal')}</p>`
    + `</details>`;
}

function shape() {
  const pg = page(), s = section();
  return `<h2>3. Shape pages and copy</h2>`
    + button(state.compact ? 'Show all section fields' : 'Focus selected section', 'toggle-sections')
    + `<p>Edit the copy and remove unneeded pages or sections. Review purpose and accessibility in Section options.</p>`
    + `<div class="wf-grid">${pagesNav()}`
    + `<section aria-label="Page wireframe"><h3>${esc(pg?.name || 'No page selected')}</h3>`
    + `<p>${esc(pg?.purpose || 'Define this page’s purpose in the page plan.')}</p>`
    + (pg ? pg.sections.map((x, i) => wire(x, i, pg)).join('') : '')
    + (pg ? addSection() : '')
    + `</section>`
    + `<aside class="wf-inspector wf-box"><h3>Section options</h3>${inspector(s)}</aside></div>`;
}

function review() {
  const p = project(), items = issues(p);
  return `<h2>4. Review the experience</h2><p>Content checks find gaps. Human review records your judgment, not accessibility certification.</p>`
    + `<p class="wf-progress">${items.length} open content checks</p>`
    + (items.length
      ? `<ul>${items.map((x, i) => `<li>${esc(x.text)} ${button('Resolve', 'resolve', `data-issue="${i}"`)}</li>`).join('')}</ul>`
      : '<p>No missing fields or unapproved sections found.</p>')
    + `<fieldset><legend>Human review</legend>`
    + checks.map((x, i) => `<label class="wf-check"><input type="checkbox" data-check="${i}" ${p.checks[i] ? 'checked' : ''}>${esc(x)}</label>`).join('')
    + `</fieldset>`
    + field('Remaining questions and design considerations', 'project.notes', p.notes, true, 'Record unresolved decisions, design questions, and caveats for review.')
    + `<p class="wf-small">Edits clear review confirmations and handoff. Keep unresolved questions explicit.</p>`
    + button('Prepare design handoff', 'step', 'data-step="4"');
}

function handoff() {
  const p = project(), count = issues(p).length, ready = !count && p.checks.every(Boolean);
  return `<h2>5. Prepare for design</h2><p>Save the reviewed plan. Visual design, accessibility, responsive behavior, implementation, and live contact testing still need verification.</p>`
    + `<div class="wf-box"><h3>${esc(p.name)}</h3>`
    + `<p>${p.pages.length} pages · ${p.pages.reduce((n, pg) => n + pg.sections.length, 0)} sections · ${count} open content checks</p>`
    + `<p>${ready ? 'Content fields and human review are complete.' : 'Resolve content checks and complete the human review before marking the plan ready.'}</p>`
    + `<p><strong>Unknowns:</strong> ${esc(p.unknowns) || 'None recorded'}</p>`
    + `<p><strong>Design questions:</strong> ${esc(p.notes) || 'None recorded'}</p>`
    + button('Mark plan ready for design', 'ready', ready ? 'class="primary"' : 'disabled')
    + `${p.handoff ? `<p>Plan marked ready: ${esc(new Date(p.handoff).toLocaleString())}. Export to keep this version.</p>` : ''}`
    + `</div><div class="wf-actions">`
    + button('Return to review', 'step', 'data-step="3"')
    + button('Export project backup', 'export')
    + button('Download design brief', 'brief-export')
    + `</div>`;
}

export function render() {
  const p = project();
  if (p && !p.pages.some(pg => pg.id === state.pageId)) state.pageId = p.pages[0]?.id;
  if (!page()?.sections.some(s => s.id === state.sectionId)) state.sectionId = page()?.sections[0]?.id;
  const banner = state.storageAlert ? `<div class="wf-box" role="alert"><strong>Storage notice:</strong> ${esc(state.storageAlert)}</div>` : '';
  if (!p) {
    app.innerHTML = banner + home();
    return;
  }
  app.innerHTML = banner
    + `<div class="wf-bar"><h2>${esc(p.name || 'Untitled project')}</h2><div class="wf-actions">`
    + button('All projects', 'home')
    + button('Undo', 'undo', state.history.length ? '' : 'disabled')
    + button('Redo', 'redo', state.redo.length ? '' : 'disabled')
    + button('Save project file', 'save-file')
    + button('Export backup', 'export')
    + `</div></div>`
    + `<nav class="wf-steps" aria-label="Project workflow">`
    + steps.map((x, i) => button(`${i + 1}. ${x}`, 'step', `data-step="${i}" ${i === state.step ? 'aria-current="step"' : ''}`)).join('')
    + `</nav>`
    + `<div id="wf-stage" tabindex="-1">${[brief, plan, shape, review, handoff][state.step]()}</div>`;
}
