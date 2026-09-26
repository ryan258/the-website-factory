"""Machine-readable results for factory.py, check_site.py, and build.py (--json).

Each error keeps its human message and gains a stable code, so an agent or CI step can
branch on the code without parsing prose. Unknown messages get a generic code rather
than being dropped.
"""
import json
import re
import sys

# Schema diagnostics from scripts/schemas.py always start with a JSON pointer ("$.pages.home"),
# so anchoring on it keeps them from matching checker prose. Without these, "$: missing name" was
# reported as a broken output reference and a wrong shape fell through to the generic code.
# ponytail: still pattern matching, one layer earlier. Typed diagnostics at each error site are
# the real fix; do that when a caller needs the field pointer as data rather than inside a string.
SCHEMA_POINTER = r'^\$[\w.\[\]]*: '
# First match wins. Keep patterns in step with the messages the checkers print.
CODES = [
    (SCHEMA_POINTER + r'expected ', 'SCHEMA_TYPE_INVALID'),
    (SCHEMA_POINTER + r'missing ', 'SCHEMA_FIELD_MISSING'),
    (SCHEMA_POINTER + r'unexpected field ', 'SCHEMA_FIELD_UNKNOWN'),
    # The value comes first in these ("$.x: 'nope' is not one of [...]"), so the phrase is not
    # anchored to the colon the way "missing" and "expected" are.
    (SCHEMA_POINTER + r'.*(must be|must not be empty|is not one of|does not match|needs at least)', 'SCHEMA_VALUE_INVALID'),
    (r'replaced as unsafe', 'OUTPUT_UNSAFE_URL'),
    (r'link to missing anchor|anchor .* must be|share an anchor', 'CONTENT_ANCHOR_INVALID'),
    (r'mailto link|tel link', 'CONTENT_CONTACT_LINK_INVALID'),
    (r'font\.\w+|no license file', 'SITE_FONT_INVALID'),
    (r'unknown selected preset', 'PRESET_UNKNOWN'),
    (r'workshop must be true or false', 'CONFIG_WORKSHOP_INVALID'),
    (r"data/site\.yaml: name .* must match", 'SITE_NAME_MISMATCH'),
    (r'unknown tone', 'PRESET_TONE_UNKNOWN'),
    (r'home and contact are required', 'PRESET_REQUIRED_PAGE_MISSING'),
    (r'a services module is required', 'PRESET_SERVICES_MISSING'),
    (r'invalid page key|Invalid preset identifier', 'PRESET_KEY_INVALID'),
    (r'exactly one hero must be first', 'PRESET_HERO_POSITION'),
    (r'unknown module|Unknown catalog module', 'MODULE_UNKNOWN'),
    (r'unknown variant', 'MODULE_VARIANT_UNKNOWN'),
    (r'requires page', 'MODULE_DEPENDENCY_MISSING'),
    (r'missing required field', 'CONTENT_FIELD_MISSING'),
    (r'must be text|content must be an object|must be an object|must be a nonempty list', 'CONTENT_TYPE_INVALID'),
    (r'items must be a nonempty list|item \d+ needs', 'CONTENT_ITEM_INVALID'),
    (r'unsupported \w+', 'CONTENT_ITEM_CHOICE_INVALID'),
    (r'missing or unsafe image', 'CONTENT_IMAGE_INVALID'),
    (r'link to omitted page|link has no content page|module links must be local', 'CONTENT_LINK_INVALID'),
    (r'needs label and url|URL must be text', 'CONTENT_ACTION_INVALID'),
    (r'title and description required', 'PAGE_METADATA_MISSING'),
    (r'placeholder domain', 'RELEASE_PLACEHOLDER_DOMAIN'),
    (r'placeholder text|To be confirmed', 'RELEASE_PLACEHOLDER_TEXT'),
    (r'no usable enquiry path', 'RELEASE_CONTACTABILITY_MISSING'),
    (r'No 404\.html in the build root', 'RELEASE_ERROR_PAGE_MISSING'),
    (r'expected one H1', 'OUTPUT_H1_COUNT'),
    (r'title must be under|description must be under', 'OUTPUT_METADATA_LENGTH'),
    (r'empty or duplicate', 'OUTPUT_METADATA_DUPLICATE'),
    (r'noindex', 'OUTPUT_ROBOTS'),
    (r'duplicate IDs', 'OUTPUT_DUPLICATE_ID'),
    (r'loads a file from another site', 'OUTPUT_EXTERNAL_RESOURCE'),
    (r'missing |broken|anchor', 'OUTPUT_REFERENCE_BROKEN'),
    (r'budget|KB|preloaded fonts', 'OUTPUT_BUDGET'),
    (r'No generated HTML', 'OUTPUT_EMPTY'),
    (r'Refusing to write generated output|symlink', 'BUILD_OUTPUT_CONFLICT'),
    (r'hugo|sass|Hugo Extended', 'BUILD_TOOL'),
]

def code_for(message):
    for pattern, code in CODES:
        if re.search(pattern, message):
            return code
    return 'ERROR'

def result(errors, **extra):
    return dict(ok=not errors, errors=[dict(code=code_for(e), message=e) for e in errors], **extra)

def emit(errors, **extra):
    """Print the JSON result on stdout; return the process exit code."""
    json.dump(result(errors, **extra), sys.stdout, indent=2)
    sys.stdout.write('\n')
    return 1 if errors else 0
