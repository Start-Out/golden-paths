import unittest
from unittest import mock

from startout.module import Module, check_for_key


class TestModuleInitializationSuccess(unittest.TestCase):
    def setUp(self):
        self.name = "successfully_initialized_module"
        self.dest = "/path/to/dest"
        self.source = "git"
        self.scripts = {'init': 'exit 0', 'destroy': 'exit 0'}
        self.dependencies = ["dependency1", "dependency2"]
        self.init_options = [{'env_name': 'test', 'type': 'str', 'default': 'default_val', 'prompt': 'prompt_msg'}]
        self.module = Module(self.name, self.dest, self.source, self.scripts, self.dependencies, self.init_options)

    def test_module_init_succeeds(self):
        try:
            self.assertIsInstance(self.module, Module, "Initialization of Module instance failed")
        except TypeError:
            self.fail("Initialization of Module instance raised TypeError")

    def test_run_missing_script(self):
        with self.assertRaises(ValueError):
            self.module.run('missing_script')

    def test_run_existing_script_no_output(self):
        response, code = self.module.run('init')
        self.assertEqual(code, 0)
        self.assertTrue(isinstance(response, str))

    def test_run_existing_script_with_output(self):
        # capture print output during method execution
        response, code = self.module.run('init', print_output=True)

        # check return from run method
        self.assertEqual(code, 0)
        self.assertTrue(isinstance(response, str))

    @mock.patch.object(Module, 'run')
    def test_initialize_success(self, mock_run):
        # arrange
        mock_run.return_value = ("init completed", 0)

        # act
        result = self.module.initialize()

        # assert
        self.assertTrue(result)
        mock_run.assert_called_once_with('init', print_output=True)

    @mock.patch.object(Module, 'run')
    def test_initialize_failure(self, mock_run):
        # arrange
        mock_run.return_value = ("init failed", 1)

        # act
        result = self.module.initialize()

        # assert
        self.assertFalse(result)
        mock_run.assert_called_once_with('init', print_output=True)

    @mock.patch.object(Module, 'run')
    def test_destroy_success(self, mock_run):
        # arrange
        mock_run.return_value = ("destroy completed", 0)

        # act
        result = self.module.destroy()

        # assert
        self.assertTrue(result)
        mock_run.assert_called_once_with('destroy', print_output=True)

    @mock.patch.object(Module, 'run')
    def test_destroy_failure(self, mock_run):
        # arrange
        mock_run.return_value = ("destroy failed", 1)

        # act
        result = self.module.destroy()

        # assert
        self.assertFalse(result)
        mock_run.assert_called_once_with('destroy', print_output=True)

class TestModuleInitializationFails(unittest.TestCase):
    def setUp(self):
        self.name = "failing_init_module"
        self.dest = "/path/to/dest"
        self.source = "git"
        self.scripts = {'init': 'init.sh'}
        self.dependencies = ["dependency1", "dependency2"]
        self.init_options = [{'env_name': 'test', 'type': 'str', 'default': 'default_val', 'prompt': 'prompt_msg'}]

    def test_module_init_fails_when_destroy_script_is_missing(self):
        with self.assertRaises(TypeError):
            Module(self.name, self.dest, self.source, self.scripts, self.dependencies, self.init_options)

class TestModuleInitializationPartial(unittest.TestCase):
    def setUp(self):
        self.name = "partial_init_module"
        self.dest = "/path/to/dest"
        self.source = "git"
        self.scripts = {'destroy': 'destroy.sh'}
        self.dependencies = ["dependency1", "dependency2"]
        self.init_options = [{'env_name': 'test', 'type': 'str', 'default': 'default_val', 'prompt': 'prompt_msg'}]

    def test_module_init_fails_when_init_script_is_missing(self):
        with self.assertRaises(TypeError):
            Module(self.name, self.dest, self.source, self.scripts, self.dependencies, self.init_options)

    def test_check_for_key_fails_without_script(self):
        with self.assertRaises(TypeError):
            check_for_key("module", "not_found", {
                "script": "exit 0"
            })


if __name__ == '__main__':
    unittest.main()