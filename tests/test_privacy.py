import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('check_privacy', Path(__file__).resolve().parents[1] / 'scripts/check_privacy.py')
privacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(privacy)


class PrivacyTests(unittest.TestCase):
    def test_detects_contacts_and_paths_without_printing_values(self):
        contact = 'private.person' + '@' + 'mail.test'
        personal_path = 'C:' + '/Users/' + 'private-person' + '/documents'
        findings = privacy.inspect('README.md', (contact + '\n' + personal_path).encode())
        self.assertEqual(len(findings), 2)
        self.assertNotIn(contact, str(findings))
        self.assertNotIn(personal_path, str(findings))

    def test_blocks_private_files(self):
        for name in ('.env', '.env.production', 'cv.pdf', 'main.tex', '.vita/config.json', '.test-artifacts/preview.png', 'private.key', 'history.bundle'):
            self.assertTrue(privacy.inspect(name, b''), name)

    def test_preserves_examples_and_original_upstream_notices(self):
        self.assertFalse(privacy.inspect('tests/example.py', b'test@example.invalid sample@example.com'))
        self.assertFalse(privacy.inspect('vita_tree/static/vendor/LICENSE', b'Original upstream attribution'))

    def test_github_generated_merge_metadata_is_public(self):
        metadata = b'Contributor <123+contributor@users.noreply.github.com>\nGitHub <noreply@github.com>\nMerge feature into main'
        self.assertFalse(privacy.inspect('pr-merge/commit-metadata', metadata))

    def test_github_service_exception_does_not_allow_personal_or_lookalike_addresses(self):
        for local, domain in [('private.person', 'github.com'), ('noreply', 'github.com.mail.test'), ('noreply', 'mail.test')]:
            address = local + '@' + domain
            with self.subTest(domain=domain):
                findings = privacy.inspect('commit-metadata', address.encode())
                self.assertEqual(len(findings), 1)
                self.assertNotIn(address, str(findings))
