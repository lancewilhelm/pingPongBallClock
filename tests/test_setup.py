import json
import os
import sys
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class SetupTests(unittest.TestCase):
    def test_rejects_unsupported_checkout_path_before_installing(self):
        with tempfile.TemporaryDirectory() as tmp:
            code = Path(tmp) / 'space in path' / 'code'
            code.mkdir(parents=True)
            shutil.copy(ROOT / 'code/setup.sh', code / 'setup.sh')
            result = subprocess.run(['bash', str(code / 'setup.sh')], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Checkout path must contain only', result.stderr)

    def test_rerun_enables_then_restarts_service(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            code = base / 'project' / 'code'
            code.mkdir(parents=True)
            for name in ('setup.sh', 'pingpongballclock.service.in', 'requirements.txt'):
                shutil.copy(ROOT / 'code' / name, code / name)
            bin_dir = base / 'bin'
            bin_dir.mkdir()
            log = base / 'commands'
            sudo = bin_dir / 'sudo'
            sudo.write_text('#!/bin/bash\nprintf "%s\\n" "$*" >> "$COMMAND_LOG"\n')
            sudo.chmod(0o755)
            python = bin_dir / 'python3'
            python.write_text('#!/bin/bash\nif [[ $1 == - ]]; then exec "$REAL_PYTHON" "$@"; fi\nmkdir -p "$3/bin"\nprintf "#!/bin/bash\\nexit 0\\n" > "$3/bin/python"\nchmod +x "$3/bin/python"\n')
            python.chmod(0o755)
            env = dict(os.environ, PATH=f'{bin_dir}:{os.environ["PATH"]}', COMMAND_LOG=str(log), REAL_PYTHON=sys.executable)
            first = subprocess.run(['bash', str(code / 'setup.sh')], env=env, check=True, capture_output=True, text=True)
            auth = code / '.local' / 'auth.json'
            credentials = json.loads(auth.read_text())
            self.assertEqual(credentials['username'], 'admin')
            self.assertIn(credentials['password'], first.stdout)
            self.assertEqual(auth.stat().st_mode & 0o777, 0o600)
            second = subprocess.run(['bash', str(code / 'setup.sh')], env=env, check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(auth.read_text()), credentials)
            self.assertNotIn(credentials['password'], second.stdout)
            commands = log.read_text().splitlines()
            systemctl = [line for line in commands if line.startswith('systemctl ')]
            self.assertEqual(systemctl, [
                'systemctl daemon-reload',
                'systemctl enable pingpongballclock.service',
                'systemctl restart pingpongballclock.service',
            ] * 2)


if __name__ == '__main__':
    unittest.main()
