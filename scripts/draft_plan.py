#!/usr/bin/env python3
"""Draft a website page plan from a written client brief with Claude.

  python3 scripts/draft_plan.py brief.md -o plan.json
  python3 scripts/from_plan.py plan.json                 # preview the compiled preset

Needs the Anthropic Python SDK (pip install -r requirements-dev.txt) and a credential:
ANTHROPIC_API_KEY, or a profile from `ant auth login`. Each run is a paid API call.

The output is a planner backup ({"version": 1, "projects": [...]}) that the /site-kit/
planner can import and scripts/from_plan.py can compile. Every section is a draft: the
model is told to use only facts in the brief and to write "To be confirmed" for anything
else, and the result still needs a person's review before any of it is published.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from from_plan import PLANNER_LABELS, TBC  # noqa: E402
from schemas import plan_schema, validate  # noqa: E402

MODEL = 'claude-opus-5'
# Planner limits (assets/js/workflow.js valid()): a draft beyond them could not be imported.
MAX_PAGES, MAX_SECTIONS, MAX_TEXT = 30, 40, 12000

SYSTEM = f"""You plan small-business websites for a web studio. Read the client brief and
propose pages and sections using only the section types in the catalog below.

Rules:
- Use only facts stated in the brief. Never invent prices, results, client names,
  testimonials, credentials, dates, addresses, hours, or statistics.
- Where a section needs a fact the brief does not give, write "{TBC}" followed by what
  is needed, for example "{TBC}: opening hours". List each such gap in "unknowns".
- List the facts you did use from the brief in "facts".
- Every page's first section is "hero". Include a "contact" page and at least one
  "services" section. Prefer fewer, clearer pages (usually 3-6).
- For sections with several items, write the body as one item per line:
  "Item title - one sentence about it".
- "variant" must be one of the section type's variants, or "" for the default.
- Write plain, specific copy in the business's voice. No filler.

Section catalog (kind: purpose; variants):
"""

def catalog(registry):
    lines = []
    allowed = plan_schema(registry)['properties']['pages']['items']['properties']['sections']['items']['properties']['kind']['enum']
    for key, module in registry.items():
        if key in allowed:
            guide = f" Copy: {module['copy_guidance']}" if module.get('copy_guidance') else ''
            lines.append(f"- {key}: {module['purpose']} ({', '.join(module['variants'])}).{guide}")
    return '\n'.join(lines)

def request(brief, registry, model=MODEL, effort='high'):
    """Send the brief; return the parsed plan dict. Raises SystemExit with a plain message on failure."""
    try:
        import anthropic
    except ImportError:
        raise SystemExit('The Anthropic SDK is not installed. Run: pip install -r requirements-dev.txt')
    schema = plan_schema(registry)
    for key in ('$schema', '$id', 'title', 'description'):
        schema.pop(key, None)
    client = anthropic.Anthropic()
    try:
        response = client.beta.messages.create(
            model=model,
            max_tokens=16000,
            betas=['server-side-fallback-2026-07-01'],
            # A declined request is retried server-side on Anthropic's recommended fallback model.
            fallbacks='default',
            thinking={'type': 'adaptive'},
            output_config={'effort': effort, 'format': {'type': 'json_schema', 'schema': schema}},
            system=SYSTEM + catalog(registry),
            messages=[{'role': 'user', 'content': f'Client brief:\n\n{brief}'}],
        )
    except anthropic.AuthenticationError:
        raise SystemExit('The API key was rejected. Set ANTHROPIC_API_KEY, or run `ant auth login`.')
    except anthropic.RateLimitError:
        raise SystemExit('Rate limited by the API. Wait a minute and try again.')
    except anthropic.APIStatusError as error:
        raise SystemExit(f'The API returned an error ({error.status_code}): {error.message}')
    except anthropic.APIConnectionError:
        raise SystemExit('Could not reach the API. Check the network connection.')
    if response.stop_reason == 'refusal':
        raise SystemExit('The model declined this brief. Review the brief and try again.')
    if response.stop_reason == 'max_tokens':
        raise SystemExit('The draft was cut off before it finished. Try a shorter brief.')
    text = next((block.text for block in response.content if block.type == 'text'), '')
    try:
        plan = json.loads(text)
    except ValueError:
        raise SystemExit('The model did not return a readable plan.')
    problems = validate(plan, schema)
    if problems:
        raise SystemExit('The draft did not match the plan format:\n  ' + '\n  '.join(problems[:10]))
    return plan

def to_planner(plan, registry, source='brief'):
    """Convert the model's plan into a planner backup the workshop can import."""
    clip = lambda value: str(value or '')[:MAX_TEXT]
    label = lambda kind: PLANNER_LABELS.get(kind, registry[kind]['name'])
    pages = []
    for page in plan['pages'][:MAX_PAGES]:
        sections = []
        for s in page['sections'][:MAX_SECTIONS]:
            section = dict(id=str(uuid.uuid4()), kind=label(s['kind']), title=clip(s['title']), body=clip(s['body']),
                           cta=clip(s['cta']), target='', a11y='', state='draft')
            if s.get('variant') in registry[s['kind']]['variants']:
                section['variant'] = s['variant']
            sections.append(section)
        pages.append(dict(id=str(uuid.uuid4()), name=clip(page['name']) or 'Page', purpose=clip(page['purpose']),
                          action=clip(page['action']), sections=sections))
    now = datetime.now(timezone.utc).isoformat()
    project = dict(
        id=str(uuid.uuid4()), name=clip(plan['name']) or 'Untitled Website', business=clip(plan['business']),
        audience=clip(plan['audience']), goal=clip(plan['goal']), scope='',
        facts=clip('\n'.join(plan['facts'])), unknowns=clip('\n'.join(plan['unknowns'])),
        notes=clip(f'AI draft from {source}, {now[:10]}. Nothing here is approved: check every fact and '
                   f'replace each "{TBC}" before publishing.'),
        updated=now, checks=[False, False, False], pages=pages)
    return {'version': 1, 'projects': [project]}

def draft(brief, registry=None, model=MODEL, effort='high', source='brief'):
    registry = registry or json.loads((ROOT / 'data/modules.json').read_text())
    return to_planner(request(brief, registry, model, effort), registry, source)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('brief', help='Text or Markdown file with the client brief')
    parser.add_argument('-o', '--output', help='Where to write the plan (default: print it)')
    parser.add_argument('--model', default=MODEL)
    parser.add_argument('--effort', default='high', choices=['low', 'medium', 'high', 'xhigh', 'max'])
    args = parser.parse_args(argv)
    brief = Path(args.brief).read_text().strip()
    if not brief:
        parser.error('The brief is empty.')
    result = draft(brief, model=args.model, effort=args.effort, source=Path(args.brief).name)
    text = json.dumps(result, indent=2, ensure_ascii=False) + '\n'
    if args.output:
        Path(args.output).write_text(text)
        project = result['projects'][0]
        gaps = text.count(TBC)
        print(f'Wrote {args.output}: {len(project["pages"])} pages, {gaps} "{TBC}" placeholder(s). '
              'Import it in /site-kit/ or compile it with scripts/from_plan.py.', file=sys.stderr)
    else:
        sys.stdout.write(text)
    return 0

if __name__ == '__main__':
    sys.exit(main())
