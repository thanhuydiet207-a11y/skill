import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from omega.context import encode, packet, gate_summary


class ContextTests(unittest.TestCase):
    def test_lossless_unicode_and_whitespace(self):
        value={'code':'  x = "Tiếng Việt"\n\treturn x\n','empty':[], 'ok':False}
        self.assertEqual(json.loads(encode(value)),json.loads(encode(value,True)))
        self.assertLess(len(encode(value,True).encode()),len(encode(value).encode()))

    def test_packet_preserves_source_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a.py').write_bytes(b'first\r\n  second\r\nthird\n')
            result=packet(p,['a.py:2:3','a.py:2:3'])
            self.assertEqual(len(result['sources']),1)
            self.assertEqual(result['sources'][0]['content'],'  second\r\nthird\n')
            self.assertEqual(result['omitted_requested_sources'],0)
            self.assertEqual(len(result['sources'][0]['source_sha256']),64)

    def test_budget_fails_without_silent_truncation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_text('x'*1000)
            with self.assertRaisesRegex(ValueError,'budget'):packet(p,['a'],100)

    def test_missing_empty_and_ranges_fail(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_text('one\ntwo\n')
            for choices in ([],['missing'],['a:2:1'],['a:1:9']):
                with self.assertRaises(ValueError):packet(p,choices)

    def test_private_binary_and_escape_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'.env').write_text('secret');(p/'binary').write_bytes(b'\0')
            (p/'escape').symlink_to('/tmp')
            for source in ('.env','.env.local','.git/config','.omega/memory/x','../outside','escape/file','binary'):
                with self.assertRaises(ValueError):packet(p,[source])

    def test_summary_keeps_failure_and_links_success(self):
        original={'passed':False,'evidence':'.omega/evidence/example.json','results':[
            {'gate':'build','exit_code':0,'output':'successful verbose log','truncated':False},
            {'gate':'tests','exit_code':1,'output':'actual assertion failure','truncated':False}]}
        result=gate_summary(original)
        self.assertEqual(result['results'][1]['output'],'actual assertion failure')
        self.assertEqual(result['results'][0]['output_ref'],'.omega/evidence/example.json#/results/0/output')
        self.assertEqual(original['results'][0]['output'],'successful verbose log')
        self.assertFalse(result['passed'])

    def test_changed_source_changes_fingerprint(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'a').write_text('first')
            before=packet(p,['a'])['sources'][0]['source_sha256']
            (p/'a').write_text('second')
            self.assertNotEqual(before,packet(p,['a'])['sources'][0]['source_sha256'])

    def test_cli_compact_preserves_default_plan(self):
        root=Path(__file__).resolve().parent.parent
        cmd=[sys.executable,'-m','omega','plan','--complexity','high']
        full=subprocess.run(cmd,cwd=root,text=True,capture_output=True,check=True).stdout
        compact=subprocess.run(cmd+['--compact'],cwd=root,text=True,capture_output=True,check=True).stdout
        self.assertEqual(json.loads(full),json.loads(compact))
        self.assertLess(len(compact.encode()),len(full.encode()))

    def test_cli_packet_budget_fails(self):
        root=Path(__file__).resolve().parent.parent
        p=subprocess.run([sys.executable,'-m','omega','context','--select','omega/context.py','--max-bytes','10'],cwd=root,text=True,capture_output=True)
        self.assertEqual(p.returncode,2)
        self.assertEqual(p.stdout,'')
        self.assertIn('budget',p.stderr)
