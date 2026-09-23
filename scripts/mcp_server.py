#!/usr/bin/env python3
"""The website factory as an MCP server (stdio, JSON-RPC 2.0, standard library only).

Claude Code picks it up from .mcp.json in the project root. Any MCP client can run:

  python3 scripts/mcp_server.py

Tools read the master and its generated output. Three have side effects, and say so:
build_site writes public/ (generated output only), create_client_site writes a new folder
outside the master, and draft_plan makes a paid Claude API call. Nothing commits, pushes,
deploys, or enables a contact form.
"""
import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import claims  # noqa: E402
import factory  # noqa: E402
import from_plan  # noqa: E402
import report  # noqa: E402
import schemas  # noqa: E402

PROTOCOL_VERSIONS = ('2025-06-18', '2025-03-26', '2024-11-05')

def registry():
    return json.loads((ROOT / 'data/modules.json').read_text())

def preset_file(slug):
    path = ROOT / 'data/presets' / f'{slug}.json'
    if not slug or '/' in slug or not path.is_file():
        raise ValueError(f'No preset named {slug!r}. Use list_presets.')
    return json.loads(path.read_text())

def run_script(*args):
    result = subprocess.run([sys.executable, str(ROOT / 'scripts' / args[0]), *args[1:]], cwd=ROOT,
                            capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except ValueError:
        return {'ok': False, 'errors': [{'code': 'ERROR', 'message': (result.stderr or result.stdout).strip()[-2000:]}]}

# --- tools -----------------------------------------------------------------------------

def list_modules():
    return {key: {'name': m['name'], 'purpose': m['purpose'], 'variants': m['variants'], 'required': m['required'],
                  'item_required': m.get('item_required', []), 'item_choices': m.get('item_choices', {}),
                  'dependencies': m.get('dependencies', [])} for key, m in registry().items()}

def list_presets():
    selected = json.loads((ROOT / 'data/factory.json').read_text())['preset']
    return [{'slug': p.stem, 'name': d['name'], 'tone': d.get('tone'), 'pages': list(d['pages']), 'selected': p.stem == selected}
            for p in sorted((ROOT / 'data/presets').glob('*.json')) for d in [json.loads(p.read_text())]]

def get_preset(slug):
    return preset_file(slug)

def get_schema(name):
    if name not in ('preset', 'plan'):
        raise ValueError('name must be "preset" or "plan".')
    return schemas.generated()[f'{name}.schema.json']

def validate_preset(preset, slug='candidate'):
    """Schema shape plus the full factory rules, without writing anything."""
    shape = schemas.validate(preset, schemas.generated()['preset.schema.json'])
    rules = factory.validate(ROOT, extra_presets={slug: preset})
    return report.result(shape + [e for e in rules if e.startswith(f'{slug}')])

def check_claims(slug=None, preset=None):
    data = preset if preset is not None else preset_file(slug or json.loads((ROOT / 'data/factory.json').read_text())['preset'])
    found = claims.find(data)
    return {'ok': all(f['approved'] for f in found), 'findings': found}

def compile_plan(plan, name=None):
    slug, preset = from_plan.convert_plan_to_preset(plan, registry())
    if name:
        slug = from_plan.slugify(name)
    result = validate_preset(preset, slug)
    return {**result, 'slug': slug, 'preset': preset}

def build_site(workshop=False):
    return run_script('build.py', '--json', *(['--workshop'] if workshop else []))

def check_site(workshop=False):
    return run_script('check_site.py', str(ROOT / ('public-workshop' if workshop else 'public')), '--json')

def create_client_site(destination, name, preset=None, plan=None):
    import factory_run
    import new_site
    if bool(preset) == bool(plan):
        raise ValueError('Give exactly one of preset (a slug) or plan (a planner export).')
    if plan:
        dest, code = factory_run.run(plan, destination, name, 'mcp plan')
        return {'ok': code == 0, 'destination': str(dest), 'review': (dest / 'docs/plan-review.md').read_text()}
    dest = new_site.create(destination, name, preset)
    return {'ok': True, 'destination': str(dest)}

def draft_plan(brief):
    import draft_plan as drafting
    return drafting.draft(brief, source='mcp brief')

TEXT, OBJECT, BOOL = {'type': 'string'}, {'type': 'object'}, {'type': 'boolean'}
def schema(required=(), **props):
    return {'type': 'object', 'properties': props, 'required': list(required), 'additionalProperties': False}

TOOLS = {
    'list_modules': (list_modules, 'List the 30 section modules: purpose, variants, required content, and dependencies.', schema()),
    'list_presets': (list_presets, 'List business presets and their pages; marks the one the live site uses.', schema()),
    'get_preset': (get_preset, 'Read one preset (pages, sections, copy) by slug.', schema(['slug'], slug=TEXT)),
    'get_schema': (get_schema, 'Get the JSON Schema for a "preset" or an AI-drafted "plan".', schema(['name'], name={'enum': ['preset', 'plan']})),
    'validate_preset': (validate_preset, 'Validate a preset object against the schema and every factory rule. Writes nothing.',
                        schema(['preset'], preset=OBJECT, slug=TEXT)),
    'check_claims': (check_claims, 'Find prices, counts, ratings, testimonials, and absolute words that need the business to confirm them. '
                     'Pass a preset slug, or a preset object.', schema([], slug=TEXT, preset=OBJECT)),
    'compile_plan': (compile_plan, 'Compile a planner export into a preset and validate it. Writes nothing.',
                     schema(['plan'], plan=OBJECT, name=TEXT)),
    'build_site': (build_site, 'Build and check the master site. Side effect: rewrites generated output in public/ (or public-workshop/).',
                   schema([], workshop=BOOL)),
    'check_site': (check_site, 'Check the last build: links, metadata, headings, robots, and size budgets.', schema([], workshop=BOOL)),
    'create_client_site': (create_client_site, 'Create a separate client copy outside the master from a preset slug or a planner export, '
                           'then build it. Side effect: writes the destination folder (which must not exist).',
                           schema(['destination', 'name'], destination=TEXT, name=TEXT, preset=TEXT, plan=OBJECT)),
    'draft_plan': (draft_plan, 'Draft a planner export from a client brief with Claude. Side effect: a paid API call; needs '
                   'ANTHROPIC_API_KEY. The draft marks unknown facts "To be confirmed" and needs human review.',
                   schema(['brief'], brief=TEXT)),
}

# --- protocol --------------------------------------------------------------------------

def handle(message):
    """Return the JSON-RPC response for one message, or None for a notification."""
    method, params, ident = message.get('method'), message.get('params') or {}, message.get('id')
    if ident is None:
        return None
    def ok(result):
        return {'jsonrpc': '2.0', 'id': ident, 'result': result}
    def error(code, text):
        return {'jsonrpc': '2.0', 'id': ident, 'error': {'code': code, 'message': text}}
    if method == 'initialize':
        asked = params.get('protocolVersion')
        return ok({'protocolVersion': asked if asked in PROTOCOL_VERSIONS else PROTOCOL_VERSIONS[0],
                   'capabilities': {'tools': {}},
                   'serverInfo': {'name': 'website-factory', 'version': '1.0.0'},
                   'instructions': 'Tools for the Hugo website factory. Never invent business facts: '
                                   'use "To be confirmed" and check_claims before anything is published.'})
    if method == 'ping':
        return ok({})
    if method == 'tools/list':
        return ok({'tools': [{'name': n, 'description': d, 'inputSchema': s} for n, (_, d, s) in TOOLS.items()]})
    if method == 'tools/call':
        name = params.get('name')
        if name not in TOOLS:
            return error(-32602, f'Unknown tool: {name}')
        function, _, input_schema = TOOLS[name]
        arguments = params.get('arguments') or {}
        problems = schemas.validate(arguments, input_schema)
        if problems:
            return ok({'content': [{'type': 'text', 'text': 'Invalid arguments: ' + '; '.join(problems)}], 'isError': True})
        try:
            # Anything a tool prints must not reach stdout, which carries the protocol.
            with contextlib.redirect_stdout(io.StringIO()):
                value = function(**arguments)
        except (ValueError, FileExistsError, SystemExit) as failure:
            return ok({'content': [{'type': 'text', 'text': str(failure)}], 'isError': True})
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return ok({'content': [{'type': 'text', 'text': f'{name} failed unexpectedly; see the server log.'}], 'isError': True})
        text = json.dumps(value, indent=2, ensure_ascii=False)
        result = {'content': [{'type': 'text', 'text': text}]}
        if isinstance(value, dict):
            result['structuredContent'] = value
        if isinstance(value, dict) and value.get('ok') is False:
            result['isError'] = True
        return ok(result)
    return error(-32601, f'Method not found: {method}')

def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            response = {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32700, 'message': 'Parse error'}}
        else:
            response = handle(message) if isinstance(message, dict) else \
                {'jsonrpc': '2.0', 'id': None, 'error': {'code': -32600, 'message': 'Invalid request'}}
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + '\n')
            sys.stdout.flush()
    return 0

if __name__ == '__main__':
    sys.exit(main())
