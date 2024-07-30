import subprocess
import unittest
from unittest import mock

from startout import util


class TestRunScriptWithEnvSubstitution(unittest.TestCase):

    @mock.patch("subprocess.run")
    @mock.patch("shutil.which")
    @mock.patch("shlex.split")
    def test_run_script_with_env_substitution_single_line_command(self, mock_split, mock_which, mock_run):
        mock_split.return_value = ["echo", "Hello"]
        mock_which.return_value = "/bin/echo"
        mock_run.return_value = mock.Mock(stdout="Hello\n", returncode=0)

        output, returncode = util.run_script_with_env_substitution("echo Hello")
        self.assertEqual(output, "Hello\n")
        self.assertEqual(returncode, 0)

    @mock.patch("subprocess.run")
    @mock.patch("shutil.which")
    @mock.patch("shlex.split")
    def test_run_script_with_env_substitution_unavailable_command(self, mock_split, mock_which, mock_run):
        mock_split.return_value = ["unavailable_command"]
        mock_which.return_value = None
        mock_run.return_value = subprocess.CompletedProcess([], stdout="unavailable_command not found", returncode=1)

        output, returncode = util.run_script_with_env_substitution("unavailable_command", True)
        self.assertEqual(output, "unavailable_command not found")
        self.assertEqual(returncode, 1)

    @mock.patch("subprocess.run")
    @mock.patch("shutil.which")
    @mock.patch("shlex.split")
    def test_run_script_with_env_substitution_command_failure(self, mock_split, mock_which, mock_run):
        mock_split.return_value = ["failing_command"]
        mock_which.return_value = "/bin/failing_command"
        mock_run.side_effect = subprocess.CalledProcessError(1, "failing_command", stderr="An error occurred")

        output, returncode = util.run_script_with_env_substitution("failing_command")
        self.assertEqual(output, "An error occurred")
        self.assertEqual(returncode, 1)


if __name__ == '__main__':
    unittest.main()
