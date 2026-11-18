(() => {
'use strict';
// Contrast uses the WCAG 2.x relative-luminance formula.
const channel = v => (v /= 255) <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
const luminance = hex => { const [r, g, b] = [1, 3, 5].map(i => channel(parseInt(hex.slice(i, i + 2), 16))); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
const contrast = (a, b) => { const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05); };
const $ = s => document.querySelector(s);

// 1. Contrast checker
const fg = $('#sg-fg'), bg = $('#sg-bg'), sample = $('#sg-contrast-sample'), contrastOut = $('#sg-contrast-result');
const paintContrast = () => {
  const r = contrast(fg.value, bg.value);
  sample.style.color = fg.value;
  sample.style.background = bg.value;
  const verdict = r >= 7 ? 'Passes AAA for body text'
    : r >= 4.5 ? 'Passes AA for body text, not AAA'
    : r >= 3 ? 'Passes only for large text'
    : 'Fails AA. Darken or lighten one color';
  contrastOut.textContent = `${r.toFixed(2)} : 1. ${verdict}.`;
};
fg.addEventListener('input', paintContrast);
bg.addEventListener('input', paintContrast);
$('#sg-contrast-reset').addEventListener('click', () => {
  fg.value = fg.dataset.theme;
  bg.value = bg.dataset.theme;
  paintContrast();
});

// 2. Spacing playground
const space = $('#sg-space'), spaceBox = $('#sg-space-box'), spaceOut = $('#sg-space-result');
const paintSpace = () => {
  const name = `--s${space.value}`;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  spaceBox.style.padding = `var(${name})`;
  spaceBox.style.gap = `var(${name})`;
  spaceOut.textContent = `${name} = ${value || 'not set'}`;
};
space.addEventListener('input', paintSpace);

// 3. Preset composer: the homepage order as a sketch
const form = $('#sg-composer'), composerOut = $('#sg-composer-json'), composerNote = $('#sg-composer-note');
const paintComposer = () => {
  const picked = [...form.querySelectorAll('input:checked')].map(input => ({ module: input.value }));
  composerOut.textContent = JSON.stringify({ pages: { home: { sections: picked } } }, null, 2);
  if (picked.length === 0) composerNote.textContent = 'Pick at least one section.';
  else if (picked.some(s => s.module === 'contact')) composerNote.textContent = `${picked.length} sections. Visitors have a contact path.`;
  else composerNote.textContent = `${picked.length} sections, but no contact section. Visitors have no clear next step.`;
};
form.addEventListener('change', paintComposer);

paintContrast();
paintSpace();
paintComposer();
})();
