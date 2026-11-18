// The planner's one mutable state, browser saving, and undo history.
import {app, KEY, MAX_BACKUP_LABEL, status} from './data.js';
import {oversize, valid} from './model.js';
import {render} from './views.js';

export const state = {
  db: {version: 1, projects: []},
  active: null, pageId: null, sectionId: null, step: 0, compact: true,
  history: [], redo: [], editUnit: null,
  storageOK: true, conflict: false, storageAlert: null, lastRaw: null,
};
export const fileHandles = new Map();

export const project = () => state.db.projects.find(p => p.id === state.active);
export const page = () => project()?.pages.find(p => p.id === state.pageId);
export const section = () => page()?.sections.find(s => s.id === state.sectionId);
export const say = t => { if (status.textContent !== t) status.textContent = t; };

// Open saved projects. Unreadable storage is left untouched and saving is switched off.
export function load() {
  try {
    state.lastRaw = localStorage.getItem(KEY);
    if (state.lastRaw) {
      const parsed = JSON.parse(state.lastRaw);
      if (!valid(parsed)) throw Error('Invalid saved project data');
      state.db = parsed;
    }
    say('Local projects ready.');
  } catch (e) {
    state.storageOK = false;
    state.storageAlert = 'Saved data could not be opened. Existing storage is untouched. Export your work before leaving; saving is unavailable.';
    say(state.storageAlert);
  }
}

export function save() {
  if (project() && oversize(project())) {
    // Refuse the edit rather than let the project grow past what its backup can restore.
    if (state.history.length) state.db = JSON.parse(state.history.pop());
    const msg = `That change was undone: this project would exceed the ${MAX_BACKUP_LABEL} backup limit. Export it, then split the work across projects.`;
    say(msg);
    render();
    return {ok: false, reason: 'oversize', message: msg};
  }
  if (project()) {
    project().updated = new Date().toISOString();
    project().view = {step: state.step, pageId: state.pageId, sectionId: state.sectionId, compact: state.compact};
  }
  if (!state.storageOK || state.conflict) {
    const msg = state.storageAlert || 'Not saved to this browser. Export a backup before leaving.';
    say(msg);
    return {ok: false, reason: 'unavailable', message: msg};
  }
  try {
    if (localStorage.getItem(KEY) !== state.lastRaw) {
      state.conflict = true;
      state.storageAlert = 'Another tab changed these projects. Export this version, then reload to open the saved version.';
      say(state.storageAlert);
      return {ok: false, reason: 'conflict', message: state.storageAlert};
    }
    state.lastRaw = JSON.stringify(state.db);
    localStorage.setItem(KEY, state.lastRaw);
    state.storageAlert = null;
    say('Saved in this browser. Export or save a file for recovery outside this browser.');
    return {ok: true};
  } catch (e) {
    state.storageOK = false;
    state.storageAlert = 'Save failed. Your edits remain on this screen. Export a backup before leaving.';
    say(state.storageAlert);
    return {ok: false, reason: 'failed', message: state.storageAlert};
  }
}

// Record an undo point. Typing in one field within 1.2 seconds counts as a single edit.
export function remember(unit = null) {
  state.redo = [];
  if (unit && state.editUnit?.key === unit && Date.now() - state.editUnit.time < 1200) {
    state.editUnit.time = Date.now();
    return;
  }
  state.editUnit = unit ? {key: unit, time: Date.now()} : null;
  const undo = app.querySelector('[data-action=undo]');
  if (undo) undo.disabled = false;
  state.history.push(JSON.stringify(state.db));
  if (state.history.length > 40) state.history.shift();
}

// Any edit clears the human review and the handoff mark.
function invalidate() {
  const p = project();
  if (p) {
    p.checks = [false, false, false];
    delete p.handoff;
  }
}

export function change(fn, redraw = true, unit = null) {
  remember(unit);
  invalidate();
  fn();
  save();
  if (redraw) render();
}
