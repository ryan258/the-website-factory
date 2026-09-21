const fs = require('node:fs');
const path = require('node:path');
const ROOT = path.resolve(__dirname, '..');
function paths(variable) {
  if (process.env[variable]) {
    const selected = JSON.parse(process.env[variable]);
    if (!Array.isArray(selected) || !selected.length || selected.some(p => typeof p !== 'string' || !/^\/(?!\/)/.test(p) || /[?#]/.test(p))) throw new Error(`${variable} must be a JSON array of local page paths`);
    return selected;
  }
  const output = path.resolve(ROOT, process.env.SITE_OUTPUT || 'public');
  const found = [];
  function visit(dir) {
    for (const entry of fs.readdirSync(dir, {withFileTypes:true})) {
      const file = path.join(dir, entry.name);
      if (entry.isDirectory()) visit(file);
      else if (entry.isFile() && entry.name === 'index.html') found.push('/' + path.relative(output, file).split(path.sep).join('/').replace(/index\.html$/, ''));
    }
  }
  visit(output);
  if (!found.length) throw new Error('No generated pages. Run python3 scripts/build.py first.');
  return found.sort();
}
module.exports = {ROOT, paths};
