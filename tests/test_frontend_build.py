"""Verify the committed production UI is self-contained and matches its sources."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import unittest

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'src/vita_tree/static'

class FrontendBuildTests(unittest.TestCase):
    def test_compiled_assets_are_packaged_without_a_node_runtime(self):
        manifest=json.loads((STATIC/'frontend-manifest.json').read_text(encoding='utf-8'))
        html=(STATIC/'index.html').read_text(encoding='utf-8')
        self.assertIn('id="react-root"',html)
        self.assertNotIn('/src/main.tsx',html)
        self.assertNotIn('localhost:5173',html)
        section=(ROOT/'pyproject.toml').read_text().split('[tool.setuptools.package-data]',1)[1]
        patterns=re.findall(r'"(static/[^\"]+)"',section)
        for name in manifest['files']:
            self.assertTrue((STATIC/name).is_file(),name)
            path=PurePosixPath('static/'+name)
            self.assertTrue(any(path.match(pattern) for pattern in patterns),'Not packaged: '+str(path))
        notices=(STATIC/'vendor/FRONTEND-LICENSE').read_text(encoding='utf-8')
        self.assertTrue(bool(re.search(r'(?m)^react \d',notices)),'Missing React runtime license')

    def test_generated_ui_matches_the_versioned_frontend_sources(self):
        manifest=json.loads((STATIC/'frontend-manifest.json').read_text(encoding='utf-8'))
        for name,expected in manifest['sources'].items():
            content=(ROOT/name).read_text(encoding='utf-8').replace('\r\n','\n')
            self.assertEqual(hashlib.sha256(content.encode()).hexdigest(),expected,'Rebuild frontend: '+name)

    def test_generated_module_imports_are_available_offline(self):
        manifest=json.loads((STATIC/'frontend-manifest.json').read_text(encoding='utf-8'))
        for name in manifest['files']:
            if not name.endswith('.js'):continue
            source=(STATIC/name).read_text(encoding='utf-8')
            for target in re.findall(r'(?:from\s*|import\s*\(?)\s*[\"\']([^\"\']+\.m?js)[\"\']',source):
                if target.startswith('/'):
                    destination=STATIC/target.lstrip('/')
                else:
                    destination=(STATIC/name).parent/target
                self.assertTrue(destination.resolve().is_relative_to(STATIC.resolve()),target)
                self.assertTrue(destination.is_file(),f'{name} imports missing {target}')
