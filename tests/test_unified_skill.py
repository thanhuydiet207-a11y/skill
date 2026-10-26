"""Migration coverage, reference integrity and the single discoverable entry."""
import json
from pathlib import Path
import tempfile
import unittest
from omega.__main__ import ENGINE_ROOT,plan
from omega.interop import compatibility
from omega.skills import MODES,assess,resources_for
from tests.skill_fixture import write_skill


class UnifiedSkill(unittest.TestCase):
    def test_only_one_skill_is_discovered_and_all_modes_are_covered(self):
        result=compatibility(ENGINE_ROOT)
        self.assertTrue(result['passed']);self.assertEqual([x['name'] for x in result['skills']],['omega'])
        self.assertEqual(result['skills'][0]['activation'],'model-eligible-or-unspecified')
        contract=assess(ENGINE_ROOT,'omega');self.assertTrue(contract['advanced_passed'])
        self.assertEqual({x['id'] for x in contract['modes']},set(MODES));self.assertEqual(len(MODES),13)

    def test_each_plan_keeps_one_entry_and_only_selected_reference_paths(self):
        for intent in ('change','investigate','verify','knowledge','evolve','interoperability'):
            result=plan('high',True,intent)
            self.assertEqual(result['skills'],['omega']);self.assertLess(len(result['references']),13)
            self.assertEqual(result['references'],[f'.claude/skills/omega/{MODES[m]["reference"]}' for m in result['modes']])
            self.assertTrue(all((ENGINE_ROOT/x).is_file() for x in result['references']))
            self.assertEqual(result['isolation'],'worktree');self.assertEqual(result['max_concurrent_agents'],2)

    def test_missing_reference_cannot_silently_remove_a_mode(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);text=write_skill(root)
            p=root/'.claude/skills/omega/SKILL.md';p.write_text(text.replace('[repo-map](references/repo-map.md)',''))
            result=assess(root,'omega');self.assertFalse(result['passed'])
            self.assertFalse(next(x for x in result['modes'] if x['id']=='repo-map')['passed'])

    def test_removed_command_or_bypass_in_mode_fails_the_entry_contract(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);write_skill(root);path=root/'.claude/skills/omega/references/quality-gates.md';original=path.read_text()
            for modified in (original.replace('python3 -m omega gates','command omitted'),original+'\nbypassPermissions'):
                path.write_text(modified);self.assertFalse(assess(root,'omega')['passed'])

    def test_mode_document_change_invalidates_bundle_without_entry_change(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);write_skill(root);before=assess(root,'omega')
            p=root/'.claude/skills/omega/references/repo-map.md';p.write_text(p.read_text()+'\nChanged guidance\n')
            after=assess(root,'omega');self.assertEqual(before['sha256'],after['sha256']);self.assertNotEqual(before['bundle_sha256'],after['bundle_sha256'])

    def test_transitive_doc_change_and_reference_cycle_are_accounted_for(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);write_skill(root);(root/'docs').mkdir()
            ref=root/'.claude/skills/omega/references/repo-map.md';ref.write_text(ref.read_text()+'\nRead docs/guide.md\n')
            guide=root/'docs/guide.md';guide.write_text('Cycle references/repo-map.md\nVersion A\n')
            before=assess(root,'omega');self.assertTrue(before['passed'])
            guide.write_text('Cycle references/repo-map.md\nVersion B\n');after=assess(root,'omega')
            self.assertNotEqual(before['bundle_sha256'],after['bundle_sha256'])
            self.assertEqual(len(after['resources']),14)

    def test_symlink_reference_is_not_certified(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);write_skill(root);p=root/'.claude/skills/omega/references/repo-map.md'
            target=root/'alternate.md';p.rename(target);p.symlink_to(target)
            result=assess(root,'omega');self.assertFalse(result['passed'])
            self.assertTrue(any(not x['available'] for x in result['resources']))

    def test_resource_count_and_aggregate_bytes_fail_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaisesRegex(ValueError,'count budget'):
                resources_for(root,'omega',' '.join('references/missing'+str(i)+'.md' for i in range(65)))
            (root/'docs').mkdir();(root/'docs/a.md').write_text('a'*600000);(root/'docs/b.md').write_text('b'*600000)
            with self.assertRaisesRegex(ValueError,'byte budget'):resources_for(root,'omega','docs/a.md docs/b.md')

    def test_old_skill_release_names_are_rejected_with_migration_hint(self):
        for name in MODES:
            with self.assertRaisesRegex(ValueError,'--skill omega'):assess(ENGINE_ROOT,name)

    def test_catalog_implemented_capabilities_resolve_inside_one_skill(self):
        catalog=json.loads((ENGINE_ROOT/'omega/catalog.json').read_text())
        for row in catalog:
            if row['state']=='implemented':
                self.assertEqual(row['skill'],'omega');self.assertEqual(row['mode'],row['name'])
                self.assertEqual(row['reference'],'.claude/skills/omega/'+MODES[row['mode']]['reference'])
            else:self.assertNotIn('skill',row)
