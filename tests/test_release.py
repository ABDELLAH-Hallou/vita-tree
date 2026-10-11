from importlib.metadata import PackageNotFoundError
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from vita_tree import __version__
from vita_tree.workspace import Workspace

spec = importlib.util.spec_from_file_location('validate_release', Path(__file__).resolve().parents[1] / 'scripts/validate_release.py')
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)


class ReleaseTests(unittest.TestCase):
    def test_tag_matches_single_version_source(self):
        self.assertEqual(release.package_version(), __version__)
        release.validate('v' + __version__, __version__)
        for tag in ('0.1.0', 'v01.1.0', 'v0.1.0rc1', 'v99.0.0', 'v1.2.3/other'):
            with self.assertRaises(ValueError):
                release.validate(tag, __version__)

    def test_installed_vita_is_used_without_local_checkout(self):
        installed = Path('/installed/site-packages').resolve()
        with patch('vita_tree.workspace.distribution', return_value=SimpleNamespace(locate_file=lambda _:installed)), patch('vita_tree.workspace.run_git', return_value='.git'):
            self.assertEqual(Workspace(Path.cwd()).vita_source, installed)
            explicit = Path('/explicit').resolve()
            self.assertEqual(Workspace(Path.cwd(), vita_source=explicit).vita_source, explicit)

    def test_base_install_does_not_require_vita(self):
        with patch('vita_tree.workspace.distribution', side_effect=PackageNotFoundError), patch('vita_tree.workspace.run_git', return_value='.git'):
            self.assertIsNone(Workspace(Path.cwd()).vita_source)
