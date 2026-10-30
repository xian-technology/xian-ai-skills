import importlib.util
import os
from pathlib import Path
import stat
import tempfile
import unittest


SCRIPT = Path(__file__).absolute().parents[1] / 'xian-node-skill/scripts/generate_validator_key.py'
spec = importlib.util.spec_from_file_location('validator_key_helper', SCRIPT)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ValidatorKeyFilesTest(unittest.TestCase):
    def test_secrets_are_private_even_with_permissive_umask(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'keys'
            previous = os.umask(0o022)
            try:
                helper.write_validator_files(target, {'priv_validator_key': {'test': True}}, force=False)
            finally:
                os.umask(previous)
            for name in ('priv_validator_key.json', 'validator_key_info.json'):
                self.assertEqual(stat.S_IMODE((target / name).stat().st_mode), 0o600)

    def test_force_does_not_follow_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            victim = target / 'existing'
            victim.write_text('unchanged')
            (target / 'priv_validator_key.json').symlink_to(victim)
            with self.assertRaises((OSError, SystemExit)):
                helper.write_validator_files(target, {'priv_validator_key': {'test': True}}, force=True)
            self.assertEqual(victim.read_text(), 'unchanged')

    def test_existing_second_file_does_not_leave_partial_first_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / 'validator_key_info.json').write_text('existing')
            with self.assertRaises(SystemExit):
                helper.write_validator_files(target, {'priv_validator_key': {'test': True}}, force=False)
            self.assertFalse((target / 'priv_validator_key.json').exists())

    def test_forced_overwrite_makes_existing_files_private(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name in ('priv_validator_key.json', 'validator_key_info.json'):
                path = target / name
                path.write_text('old')
                path.chmod(0o644)
            helper.write_validator_files(target, {'priv_validator_key': {'test': True}}, force=True)
            for name in ('priv_validator_key.json', 'validator_key_info.json'):
                self.assertEqual(stat.S_IMODE((target / name).stat().st_mode), 0o600)
