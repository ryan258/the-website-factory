"""Shared source scope, effective settings, and revision-bound build evidence.

Receipts describe local evidence, not owner approval. No credentials or source copy
are included in the public release identifier.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import tomllib

import claims

INPUT_DIRS = ('assets', 'content', 'data', 'layouts', 'static', 'functions', 'scripts')
INPUT_FILES = ('hugo.toml', '.hugo-version', '.sass-version', 'wrangler.toml')
RECEIPT = '.factory-receipt.json'
RELEASE = 'factory-release.json'


def hash_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def settings(root, env=None, base_url=None, workshop=None):
    env = os.environ if env is None else env
    unsupported = sorted(key for key in env if key in ('HUGO_CONFIG', 'HUGO_DATADIR', 'HUGO_CONTENTDIR', 'HUGO_LAYOUTDIR',
                                                       'HUGO_STATICDIR', 'HUGO_THEMESDIR', 'HUGO_PARAMS'))
    if unsupported:
        raise ValueError('Untracked Hugo source/settings overrides: ' + ', '.join(unsupported) + '. Use the project files and supported build flags.')
    config = tomllib.loads((Path(root) / 'hugo.toml').read_text())
    params = {key.lower(): value for key, value in config.get('params', {}).items()}
    def boolean(key, default):
        value = env.get('HUGO_PARAMS_' + key.upper(), params.get(key, default))
        if isinstance(value, bool):
            return value
        if str(value).lower() not in ('true', 'false'):
            raise ValueError(f'{key} must be true or false')
        return str(value).lower() == 'true'
    factory = json.loads((Path(root) / 'data/factory.json').read_text())
    preset = selected(root)
    deployment_file = Path(root) / 'wrangler.toml'
    deployment = tomllib.loads(deployment_file.read_text()) if deployment_file.is_file() else {}
    return dict(noindex=boolean('noindex', True), form_enabled=boolean('formenabled', False),
                form_action=env.get('HUGO_PARAMS_FORMACTION', params.get('formaction', '')).strip(),
                base_url=base_url or env.get('HUGO_BASEURL', config.get('baseURL', '')),
                language=env.get('HUGO_LANGUAGECODE', config.get('languageCode', 'en')),
                intake_enabled=str(deployment.get('vars', {}).get('ENQUIRY_ENABLED', 'not set')).lower(),
                override_digests={key: hashlib.sha256(str(value).encode()).hexdigest() for key, value in env.items() if key.startswith('HUGO_')},
                contact_mode=preset.get('contact_mode', 'off' if preset.get('site_type') == 'creator' else 'inquiry'),
                workshop=factory.get('workshop', False) if workshop is None else workshop)


def selected(root):
    config = json.loads((Path(root) / 'data/factory.json').read_text())
    return json.loads((Path(root) / 'data/presets' / f"{config['preset']}.json").read_text())


def source_inventory(root):
    root = Path(root)
    paths = [root / name for name in INPUT_FILES if (root / name).is_file()]
    for name in INPUT_DIRS:
        paths.extend(p for p in (root / name).rglob('*') if p.is_file()
                     and '__pycache__' not in p.parts and p.suffix not in ('.pyc', '.pyo'))
    return {p.relative_to(root).as_posix(): file_hash(p) for p in sorted(paths)}


def readiness(root, preset=None):
    """Identical full-site content scope for build, status, MCP and handover."""
    preset = selected(root) if preset is None else preset
    findings = claims.find(preset, root=root)
    strings = list(claims.rendered_strings(preset)) + list(claims.site_strings(root)) + list(claims.content_strings(preset, root))
    gaps = sorted({path for path, _, text in strings if re.search(r'(?i)to be confirmed|lorem ipsum|example\.invalid', text)})
    fields = {path: hashlib.sha256(text.encode()).hexdigest() for path, _, text in strings}
    # Claims deliberately skip URLs and contact addresses. Review must still be
    # invalidated when those destinations, page order, or assets change.
    def walk(value, path):
        if isinstance(value, str):
            fields[path] = hashlib.sha256(value.encode()).hexdigest()
        elif isinstance(value, dict):
            for key, item in value.items():
                walk(item, f'{path}.{key}')
        elif isinstance(value, list):
            for i, item in enumerate(value):
                walk(item, f'{path}[{i}]')
    walk(preset['pages'], 'pages')
    for key in {spec['content'] for page in preset['pages'].values() for spec in page['sections']}:
        walk(preset['sections'][key], f'sections.{key}')
    for name in ('data/site.yaml', 'data/contact.yaml'):
        if (Path(root) / name).is_file():
            fields[name] = file_hash(Path(root) / name)
    from factory import referenced_assets
    for name in referenced_assets(preset, Path(root) / 'content'):
        asset = Path(root) / 'assets' / name
        if asset.is_file():
            fields['assets/' + name] = file_hash(asset)
    review_path = Path(root) / 'data/content-review.json'
    try:
        review = json.loads(review_path.read_text())
    except (OSError, ValueError):
        review = {}
    if not isinstance(review, dict):
        review = {}
    approved = review.get('fields', {}) if review.get('version') == 1 else {}
    if not isinstance(approved, dict):
        approved = {}
    changed = sorted(path for path, digest in fields.items() if approved.get(path) != digest)
    review_current = bool(review.get('reviewer') and review.get('reviewed_at')) and not changed
    return dict(scope='site', findings=findings, open_claims=[f for f in findings if not f['approved']], placeholders=gaps,
                fields=fields, changed_fields=changed, content_review_current=review_current)


def write_receipt(root, output, effective, inputs):
    if source_inventory(root) != inputs:
        raise ValueError('Source changed during the build. Rebuild the saved revision before publishing output.')
    if any((output / name).exists() for name in (RECEIPT, RELEASE, '.factory-build.json', '.factory-build.lock')):
        raise ValueError('Static sources contain a reserved factory receipt or release filename.')
    artifacts = {p.relative_to(output).as_posix(): file_hash(p) for p in sorted(output.rglob('*')) if p.is_file()}
    release_id = hash_json(dict(inputs=inputs, settings=effective, artifacts=artifacts))
    (output / RELEASE).write_text(json.dumps(dict(version=1, release_id=release_id)) + '\n')
    artifacts[RELEASE] = file_hash(output / RELEASE)
    receipt = dict(version=1, release_id=release_id, source_digest=hash_json(inputs), inputs=inputs,
                   settings=effective, artifacts=artifacts,
                   tools={name: (Path(root) / pin).read_text().strip()
                          for name, pin in [('hugo', '.hugo-version'), ('sass', '.sass-version')]})
    (output / RECEIPT).write_text(json.dumps(receipt, indent=2) + '\n')
    return receipt


def build_evidence(root, output):
    errors = []
    try:
        receipt = json.loads((Path(output) / RECEIPT).read_text())
        if receipt.get('version') != 1 or not isinstance(receipt.get('settings'), dict):
            raise ValueError('unsupported receipt')
        if not all(key in receipt['settings'] for key in ('noindex', 'form_enabled', 'base_url', 'contact_mode')):
            raise ValueError('incomplete effective settings')
        if hash_json(source_inventory(root)) != receipt['source_digest']:
            errors.append('Source has changed since this build. Rebuild before handover.')
        for name, expected in receipt['artifacts'].items():
            path = Path(output) / name
            if Path(name).is_absolute() or '..' in Path(name).parts or path.is_symlink():
                raise ValueError('unsafe artifact path')
            if not path.is_file() or file_hash(path) != expected:
                errors.append(f'Build artifact changed or missing: {name}')
        release = json.loads((Path(output) / RELEASE).read_text())
        if release.get('release_id') != receipt['release_id']:
            errors.append('Public release identifier does not match the build receipt.')
        return receipt, errors
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return None, ['No valid build receipt found. Rebuild to record source and output evidence.']
