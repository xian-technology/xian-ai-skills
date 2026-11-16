import importlib.util
import contextlib
import io
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).absolute().parents[1] / 'xian-node-skill/scripts/generate_validator_key.py'
spec = importlib.util.spec_from_file_location('validator_key_helper', SCRIPT)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ValidatorKeyFilesTest(unittest.TestCase):
    def test_cli_reads_existing_seed_from_a_file_without_printing_it(self):
        seed = '11' * 32
        with tempfile.TemporaryDirectory() as directory:
            seed_file = Path(directory) / 'seed.txt'
            seed_file.write_text(seed + '\n')
            output = Path(directory) / 'keys'
            argv = ['generate_validator_key.py', '--private-key-file', str(seed_file), '--out-dir', str(output)]
            payload = {'priv_validator_key': {'test': True}}
            stdout = io.StringIO()
            with patch('sys.argv', argv), patch.object(helper, 'build_validator_material', return_value=payload) as build, contextlib.redirect_stdout(stdout):
                helper.main()
            build.assert_called_once_with(seed)
            self.assertTrue((output / 'priv_validator_key.json').is_file())
            self.assertNotIn(seed, stdout.getvalue())

    def test_cli_refuses_an_inline_private_seed(self):
        argv = ['generate_validator_key.py', '--private-key', '11' * 32]
        stderr = io.StringIO()
        with patch('sys.argv', argv), patch.object(helper, 'build_validator_material', return_value={}) as build, contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                helper.main()
        self.assertEqual(error.exception.code, 2)
        self.assertIn('unrecognized arguments: --private-key', stderr.getvalue())
        build.assert_not_called()

    def test_cli_reports_an_unreadable_seed_file_without_generating_a_key(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = ['generate_validator_key.py', '--private-key-file', str(Path(directory) / 'missing')]
            stderr = io.StringIO()
            with patch('sys.argv', argv), patch.object(helper, 'build_validator_material') as build, contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as error:
                    helper.main()
            self.assertEqual(error.exception.code, 2)
            self.assertIn('Cannot read private key file.', stderr.getvalue())
            build.assert_not_called()

    def test_cli_can_generate_fresh_material_and_a_genesis_entry(self):
        payload = {'priv_validator_key': {'address': 'AB', 'pub_key': {'value': 'public'}}}
        argv = ['generate_validator_key.py', '--genesis-entry', '--power', '7', '--name', 'node-a']
        stdout = io.StringIO()
        with patch('sys.argv', argv), patch.object(helper, 'build_validator_material', return_value=payload) as build, contextlib.redirect_stdout(stdout):
            helper.main()
        build.assert_called_once_with(None)
        self.assertIn('"power": "7"', stdout.getvalue())
        self.assertIn('"name": "node-a"', stdout.getvalue())

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

    def test_key_directory_can_have_missing_parent_directories(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'nested' / 'keys'
            helper.write_validator_files(target, {'priv_validator_key': {'test': True}}, force=False)
            self.assertTrue((target / 'priv_validator_key.json').is_file())

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
