#!/usr/bin/env python3
"""The MCP server speaks JSON-RPC over stdio and its tools answer correctly."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import draft_plan  # noqa: E402

class Session:
    def __init__(self):
        self.process = subprocess.Popen([sys.executable, str(ROOT / 'scripts/mcp_server.py')], cwd=ROOT,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.next_id = 0

    def send(self, method, params=None, notify=False):
        message = {'jsonrpc': '2.0', 'method': method, 'params': params or {}}
        if not notify:
            self.next_id += 1
            message['id'] = self.next_id
        self.process.stdin.write(json.dumps(message) + '\n')
        self.process.stdin.flush()
        return None if notify else json.loads(self.process.stdout.readline())

    def call(self, tool, /, **arguments):
        return self.send('tools/call', {'name': tool, 'arguments': arguments})['result']

    def close(self):
        self.process.stdin.close()
        self.process.wait(timeout=30)
        self.process.stdout.close()
        self.process.stderr.close()

class MCPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = Session()
        cls.init = cls.session.send('initialize', {'protocolVersion': '2025-06-18', 'capabilities': {},
                                                   'clientInfo': {'name': 'test', 'version': '0'}})
        cls.session.send('notifications/initialized', notify=True)

    @classmethod
    def tearDownClass(cls):
        cls.session.close()

    def test_handshake_and_tool_list(self):
        self.assertEqual(self.init['result']['protocolVersion'], '2025-06-18')
        self.assertIn('tools', self.init['result']['capabilities'])
        tools = {t['name']: t for t in self.session.send('tools/list')['result']['tools']}
        for name in ('list_modules', 'validate_preset', 'check_claims', 'compile_plan', 'build_site', 'create_client_site', 'draft_plan'):
            self.assertIn(name, tools)
            self.assertEqual(tools[name]['inputSchema']['type'], 'object')
        self.assertIn('paid', tools['draft_plan']['description'])
        self.assertEqual(self.session.send('ping')['result'], {})

    def test_read_tools(self):
        presets = json.loads(self.session.call('list_presets')['content'][0]['text'])
        self.assertTrue(any(p['slug'] == '258webco' and p['selected'] for p in presets))
        modules = self.session.call('list_modules')['structuredContent']
        self.assertIn('split', modules['hero']['variants'])
        self.assertEqual(self.session.call('get_schema', name='plan')['structuredContent']['type'], 'object')

    def test_validate_preset_reports_codes(self):
        preset = json.loads((ROOT / 'data/presets/agency.json').read_text())
        self.assertFalse(self.session.call('validate_preset', preset=preset).get('isError'))
        preset['pages']['home']['sections'][0]['variant'] = 'nope'
        result = self.session.call('validate_preset', preset=preset)
        self.assertTrue(result['isError'])
        codes = {e['code'] for e in result['structuredContent']['errors']}
        self.assertIn('MODULE_VARIANT_UNKNOWN', codes)

    def test_compile_plan_and_claims(self):
        registry = json.loads((ROOT / 'data/modules.json').read_text())
        plan = draft_plan.to_planner(json.loads((ROOT / 'evals/recorded/bakery.json').read_text()), registry)
        result = self.session.call('compile_plan', plan=plan)['structuredContent']
        self.assertTrue(result['ok'], result['errors'])
        self.assertEqual(result['slug'], 'rise-crumb-bakery')
        self.assertTrue(self.session.call('check_claims', slug='258webco')['structuredContent']['ok'])

    def test_bad_input_is_a_tool_error_not_a_crash(self):
        self.assertTrue(self.session.call('get_preset', slug='../../etc')['isError'])
        self.assertTrue(self.session.call('get_preset')['isError'])
        self.assertIn('error', self.session.send('tools/call', {'name': 'nope', 'arguments': {}}))
        self.assertEqual(self.session.send('no/such/method')['error']['code'], -32601)

    def test_create_client_site_from_preset(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.session.call('create_client_site', destination=str(Path(tmp) / 'copy'), name='Tool Co', preset='contractor')
            self.assertFalse(result.get('isError'), result)
            self.assertTrue((Path(tmp) / 'copy/data/presets/contractor.json').is_file())

    def test_mcp_config_points_at_the_server(self):
        config = json.loads((ROOT / '.mcp.json').read_text())['mcpServers']['website-factory']
        self.assertEqual(config['args'], ['scripts/mcp_server.py'])

if __name__ == '__main__':
    unittest.main()
