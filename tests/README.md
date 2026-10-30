# Helper script tests

Run `python3 -m unittest discover -s tests` from the repository root.

The validator-key file tests use dummy JSON, temporary directories and explicit
POSIX modes. They check private permissions, forced overwrites, symlink refusal
and preflight handling when an output file already exists. They do not generate
or print private signing keys.
