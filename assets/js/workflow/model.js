// Planner rules on plain project data: validation, completeness, and starter conversion.
// No DOM access and no shared state, so each rule reads on its own.
import {CAPACITY, kinds, legacy, library, registry, starters} from './data.js';

export const uid = () => crypto.randomUUID();
export const backup = p => JSON.stringify({version: 1, projects: [p]}, null, 2);
export const bytes = text => new Blob([text]).size;
export const oversize = p => bytes(backup(p)) > CAPACITY;

export const starterSummary = preset =>
  `${preset.description || 'A complete example composition ready to shape.'} `
  + `${Object.keys(preset.pages || {}).length} pages · `
  + `${Object.values(preset.pages || {}).reduce((count, page) => count + (page.sections || []).length, 0)} sections.`;

// The editable paragraph of a structured section: its intro, else its body, else none.
export const bodyField = s => s.content ? ['intro', 'body'].find(k => Object.hasOwn(s.content, k)) : null;
export const hasBody = s => !s.content || !!bodyField(s);

export function missingCopy(s) {
  const text = v => typeof v === 'string' && v.trim(), c = s.content, m = library[s.kind];
  if (!text(s.title) || (hasBody(s) && !text(s.body))) return true;
  if (!c) return false;
  const emptyField = k => Array.isArray(c[k]) ? !c[k].length
    : typeof c[k] === 'object' ? !c[k]?.label || !c[k]?.url
    : !text(c[k]);
  const emptyItem = i => ['title', 'text', ...(m.item_required || [])].some(k => !text(i[k]));
  return m.required.some(emptyField) || (Array.isArray(c.items) ? c.items : []).some(emptyItem);
}

// Structured content: plain strings, arrays and objects only, bounded in depth and size.
export function contentValid(value, depth = 0) {
  if (depth > 8) return false;
  if (typeof value === 'string') return value.length <= 12000;
  if (Array.isArray(value)) return value.length <= 40 && value.every(v => contentValid(v, depth + 1));
  return !!value && typeof value === 'object' && Object.keys(value).length <= 80
    && Object.entries(value).every(([k, v]) => !['__proto__', 'prototype', 'constructor'].includes(k) && contentValid(v, depth + 1));
}

export function contentLeaves(value, path = []) {
  if (typeof value === 'string') return [[path, value]];
  return Object.entries(value).flatMap(([k, v]) => contentLeaves(v, [...path, k]));
}

export const contentLabel = path => path.map(k => /^\d+$/.test(k) ? Number(k) + 1 : k.replace(/([A-Z])/g, ' $1')).join(' · ');

// A backup this planner can open: the same limits apply on import, reload and export.
export function valid(data) {
  if (!data || data.version !== 1 || !Array.isArray(data.projects) || data.projects.length > 100) return false;
  const ids = new Set();
  const idOK = id => typeof id === 'string' && id.length > 0 && !ids.has(id) && !!ids.add(id);
  const strings = (o, keys) => o && keys.every(k => typeof o[k] === 'string' && o[k].length <= 12000);
  const optionalText = (v, max = 12000) => v === undefined || (typeof v === 'string' && v.length <= max);
  const optionalSlug = v => v === undefined || (typeof v === 'string' && /^[a-z0-9][a-z0-9-]{0,60}$/.test(v));
  const sectionOK = s => idOK(s.id)
    && strings(s, ['kind', 'title', 'body', 'cta', 'target', 'a11y', 'state'])
    && (s.content === undefined || (s.contentVersion === 1 && s.content && typeof s.content === 'object'
      && !Array.isArray(s.content) && contentValid(s.content)))
    && optionalText(s.variant, 80)
    && kinds.includes(s.kind)
    && optionalText(s.proposal)
    && optionalSlug(s.anchor)
    && (s.services === undefined || (Array.isArray(s.services) && s.services.length <= 40
      && s.services.every(x => typeof x === 'string' && x.length <= 12000)))
    && (s.items === undefined || (Array.isArray(s.items) && s.items.length <= 40
      && s.items.every(it => it && typeof it === 'object' && !Array.isArray(it) && contentValid(it))))
    && ['missing', 'draft', 'approved'].includes(s.state);
  const pageOK = pg => idOK(pg.id)
    && strings(pg, ['name', 'purpose', 'action'])
    && optionalSlug(pg.slug)
    && Array.isArray(pg.sections) && pg.sections.length <= 40
    && pg.sections.every(sectionOK);
  const projectOK = p => idOK(p.id)
    && strings(p, ['name', 'business', 'audience', 'goal', 'scope', 'facts', 'unknowns', 'notes', 'updated'])
    && ['tone', 'label', 'palette', 'font_pairing', 'site_type', 'contact_mode'].every(k => optionalText(p[k]))
    && (p.starterPreset === undefined || (typeof p.starterPreset === 'string' && Object.hasOwn(starters, p.starterPreset)))
    && Array.isArray(p.checks) && p.checks.length === 3 && p.checks.every(x => typeof x === 'boolean')
    && Array.isArray(p.pages) && p.pages.length <= 30
    && p.pages.every(pageOK);
  return data.projects.every(projectOK);
}

export const freshSection = kind => ({id: uid(), kind, title: '', body: '', cta: '', target: '', a11y: '', state: 'missing'});
export const freshPage = name => ({id: uid(), name, purpose: '', action: '', sections: [freshSection('Introduction')]});

export function starterSection(preset, spec) {
  const content = preset.sections?.[spec.content] || {}, definition = registry[spec.module] || {};
  const kind = legacy[spec.module] || definition.name || spec.module;
  const action = content.action || {};
  const alternatives = Array.isArray(content.items)
    ? content.items.filter(item => item.imageAlt).map(item => `${item.title || 'Image'} alt: ${item.imageAlt}`) : [];
  const a11y = [
    spec.variant ? `Selected layout: ${spec.variant}.` : '',
    definition.a11y_guidance || '',
    content.imageAlt ? `Lead image alt: ${content.imageAlt}` : '',
    ...alternatives,
  ].filter(Boolean).join('\n').slice(0, 12000);
  const section = {id: uid(), kind, variant: spec.variant || '', title: content.title || content.label || definition.name || kind,
    body: content.intro ?? content.body ?? '', cta: action.label || '', target: action.url || '', a11y, state: 'draft'};
  section.contentVersion = 1;
  section.content = JSON.parse(JSON.stringify(content));
  // An anchor is the address of this section; losing it breaks every link written against it.
  if (typeof spec.anchor === 'string' && spec.anchor) section.anchor = spec.anchor;
  return section;
}

// Open content checks for a project, each pointing at the step (and page or section) to fix it.
export function issues(p) {
  const out = [];
  for (const [key, label] of [['business', 'Business description'], ['audience', 'Audience'], ['goal', 'Visitor goal'],
    ['scope', 'Agreed scope'], ['facts', 'Confirmed business facts']]) {
    if (!p[key].trim()) out.push({text: label + ' is missing.', step: 0});
  }
  if (!p.pages.length) out.push({text: 'Add at least one page.', step: 1});
  for (const pg of p.pages) {
    if (!pg.name.trim() || !pg.purpose.trim() || !pg.action.trim()) {
      out.push({text: `${pg.name || 'Untitled page'} needs a name, purpose, and primary action.`, step: 1, page: pg.id});
    }
    if (!pg.sections.length) out.push({text: `${pg.name} has no sections.`, step: 2, page: pg.id});
    for (const s of pg.sections) {
      const label = pg.name + ' / ' + s.kind, at = {step: 2, page: pg.id, section: s.id};
      if (missingCopy(s)) out.push({text: label + ' has missing copy.', ...at});
      if (s.state !== 'approved') out.push({text: label + ' copy needs approval.', ...at});
      if (s.cta.trim() && !s.target.trim()) out.push({text: label + ' needs a destination for its action.', ...at});
      if (!s.a11y.trim()) out.push({text: label + ' needs accessibility and image notes (or an explicit “not needed”).', ...at});
    }
  }
  return out;
}

export function move(list, id, delta) {
  const i = list.findIndex(x => x.id === id), j = i + delta;
  if (i >= 0 && j >= 0 && j < list.length) [list[i], list[j]] = [list[j], list[i]];
}
