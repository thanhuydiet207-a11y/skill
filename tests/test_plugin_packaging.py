"""Plugin distribution contracts and cache/target boundaries, without a model call."""
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from benchmarks.plugin_packaging import export_plugin
from omega import __version__
from omega.__main__ import ENGINE_ROOT
from omega.policy import explain
from omega.skills import suite_digest


class PluginPackaging(unittest.TestCase):
    def test_manifest_preserves_one_skill_and_uses_standard_agent_directory(self):
        manifest=json.loads((ENGINE_ROOT/'.claude-plugin/plugin.json').read_text())
        self.assertEqual(manifest['name'],'omega');self.assertEqual(manifest['version'],__version__)
        self.assertEqual(manifest['skills'],'./.claude/skills/')
        self.assertEqual(len(list((ENGINE_ROOT/manifest['skills']).glob('*/SKILL.md'))),1)
        self.assertEqual(len(list((ENGINE_ROOT/'agents').glob('*.md'))),3)
        for field in ('agents','hooks','mcpServers','permissions','userConfig'):self.assertNotIn(field,manifest)

    def test_marketplace_installs_this_repository_root_and_matching_version(self):
        marketplace=json.loads((ENGINE_ROOT/'.claude-plugin/marketplace.json').read_text())
        manifest=json.loads((ENGINE_ROOT/'.claude-plugin/plugin.json').read_text())
        self.assertEqual(marketplace['name'],'omega-marketplace');self.assertEqual(len(marketplace['plugins']),1)
        plugin=marketplace['plugins'][0]
        self.assertEqual(plugin['source'],'./');self.assertEqual(plugin['name'],manifest['name']);self.assertEqual(plugin['version'],manifest['version'])

    def fixture(self,root):
        subprocess.run(['git','init','-q'],cwd=root,check=True)
        files={'.gitignore':'.omega/\nnode_modules/\n','.claude-plugin/plugin.json':'{}',
               '.claude-plugin/marketplace.json':'{}','.claude/skills/omega/SKILL.md':'Fixture only','omega_cli.py':'# fixture entry'}
        for name,text in files.items():
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        subprocess.run(['git','add','.'],cwd=root,check=True)
        base=root/'.omega/plugin-packaging/export';base.mkdir(parents=True)
        return base

    def test_archive_excludes_untracked_runtime_and_dependencies(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=self.fixture(root)
            (root/'.omega/private-state').write_text('local state, never export')
            (root/'node_modules').mkdir();(root/'node_modules/runtime').write_text('ignored dependency')
            (root/'notes.txt').write_text('untracked user note')
            payload,archive,manifest=export_plugin(root,base)
            with zipfile.ZipFile(archive) as bundle:
                self.assertEqual(set(bundle.namelist()),{x['path'] for x in manifest})
                for row in manifest:self.assertEqual(hashlib.sha256(bundle.read(row['path'])).hexdigest(),row['sha256'])
                self.assertFalse(any('.omega' in p.split('/') or 'node_modules' in p.split('/') or p=='notes.txt' for p in bundle.namelist()))
            self.assertTrue((payload/'omega_cli.py').is_file())

    def test_archive_excludes_tracked_eval_suite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=self.fixture(root)
            (root/'evals/case').mkdir(parents=True);(root/'evals/case/case.yaml').write_text('name: case\n')
            subprocess.run(['git','add','evals'],cwd=root,check=True)
            payload,archive,manifest=export_plugin(root,base)
            self.assertFalse(any(row['path'].startswith('evals/') for row in manifest))
            self.assertFalse((payload/'evals').exists())

    def test_archive_refuses_tracked_symlinks(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);base=self.fixture(root);(root/'alias.py').symlink_to(root/'omega_cli.py')
            subprocess.run(['git','add','alias.py'],cwd=root,check=True)
            with self.assertRaisesRegex(ValueError,'Symlink'):export_plugin(root,base)

    def test_relocated_cli_does_not_import_target_omega_or_write_cache(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);engine=base/'installed plugin';engine.mkdir();target=base/'target project';target.mkdir()
            shutil.copyfile(ENGINE_ROOT/'omega_cli.py',engine/'omega_cli.py')
            shutil.copytree(ENGINE_ROOT/'omega',engine/'omega',ignore=shutil.ignore_patterns('__pycache__'))
            (target/'omega.py').write_text('raise RuntimeError("wrong application package imported")\n')
            subprocess.run(['git','init','-q'],cwd=target,check=True)
            result=subprocess.run([sys.executable,str(engine/'omega_cli.py'),'--project-root',str(target),'map','--compact'],cwd=target,text=True,capture_output=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr);self.assertIn('omega.py',{x['path'] for x in json.loads(result.stdout)['files']})
            self.assertEqual(list(engine.rglob('__pycache__')),[])

    def test_policy_protects_plugin_metadata_and_agent_prompts(self):
        for name in ('.claude-plugin/plugin.json','.claude-plugin/marketplace.json','agents/omega-engineer.md'):
            result=explain({'hook_event_name':'PreToolUse','cwd':str(ENGINE_ROOT),'tool_name':'Write','tool_input':{'file_path':name}})
            self.assertFalse(result['allowed'])

    def test_bytecode_flag_keeps_trusted_runner_boundary(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);prefix=f'python3 -B {shlex.quote(str(ENGINE_ROOT/"omega_cli.py"))} --project-root {shlex.quote(str(root))}'
            payload={'hook_event_name':'PreToolUse','cwd':str(root),'tool_name':'Bash','tool_input':{'command':prefix+' map --compact'}}
            self.assertTrue(explain(payload,root)['allowed'])
            for command in ('python3 -B -c "print(1)"','python3 -B /tmp/untrusted.py map',prefix+' map; echo unsafe'):
                payload['tool_input']['command']=command;self.assertFalse(explain(payload,root)['allowed'])

    def test_suite_hash_binds_plugin_metadata_and_agent_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);before=suite_digest(root);(root/'.claude-plugin').mkdir();(root/'.claude-plugin/plugin.json').write_text('{}')
            after=suite_digest(root);self.assertNotEqual(before,after);(root/'agents').mkdir();(root/'agents/worker.md').write_text('Changed policy')
            self.assertNotEqual(after,suite_digest(root))
