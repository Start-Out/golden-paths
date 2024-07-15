import itertools
import os
import sys
from typing import TextIO

import yaml
from dotenv import load_dotenv
from schema import Schema, And, Or, Optional, Use

from startout.module import Module, create_module
from startout.tool import Tool


class Starter:
    """
    Starter class

    The Starter class is used to install modules and tools required for a project. It allows for easy management of
    module and tool dependencies.

    Use:
        1. use parse_starterfile on a valid Starterfile.yaml to generate a Starter
        2. use Starter.get_init_options() to collect any init options that the Starterfile may have
        3. use Starter.set_init_options() to set any init options
        4. use Starter.up() to perform the initialization of the project

    Attributes:
        starterfile_schema (Schema): Schema definition for the starter file.

    Methods:
        __init__(modules, tools, module_dependencies, tool_dependencies)
            Initializes a new instance of the Starter class.

            Parameters:
                modules (list[Module]): List of modules to be installed.
                tools (list[Tool]): List of tools to be installed.
                module_dependencies (list[list[str]]): List of module dependencies in layers.
                tool_dependencies (list[list[str]]): List of tool dependencies in layers.

        up(teardown_on_failure=True)
            Installs the modules and tools.

            Parameters:
                teardown_on_failure (bool, optional): Specifies whether to rollback successfully installed tools or
                 modules if any others fail.
                Defaults to True.

            Returns:
                bool: True if installation is successful, False otherwise.

        install_tools(teardown_on_failure=True)
            Installs the tools. Called by up().

            Parameters:
                teardown_on_failure (bool, optional): Specifies whether to rollback installations on failure.
                Defaults to True.

            Returns:
                bool: True if installation is successful, False otherwise.

        install_modules(teardown_on_failure=True)
            Installs the modules. Called by up().

            Parameters:
                teardown_on_failure (bool, optional): Specifies whether to rollback installations on failure.
                Defaults to True.

            Returns:
                bool: True if installation is successful, False otherwise.

        get_init_options()
            Placeholder method for getting the initialization options.

        set_init_options(options)
            Placeholder method for setting the initialization options.
    """
    starterfile_schema = Schema(
        {
            "tools": And(dict, len),
            "modules": And(dict, len),
            Optional('env_file'): And(Or(Use(list), None))
        }
    )

    def __init__(self, modules: list[Module], tools: list[Tool], module_dependencies: list[list[str]],
                 tool_dependencies: list[list[str]]):
        """
        Initializes the class instance with given modules, tools, module dependencies, and tool dependencies.

        :param modules: A list of Module objects representing the parsed modules.
        :param tools: A list of Tool objects representing the parsed tools.
        :param module_dependencies: A list of lists of strings representing the dependencies between modules.
            Each inner list depends on one or more of the modules in the previous inner list (the first list has no
            dependencies).
        :param tool_dependencies: A list of lists of strings representing the dependencies between tools.
            Each inner list depends on one or more of the modules in the previous inner list (the first list has no
            dependencies).
        """
        self.modules = modules
        self.tools = tools
        self.module_dependencies = module_dependencies
        self.tool_dependencies = tool_dependencies

    def up(self, teardown_on_failure=True, fail_early=True):
        """
        :param teardown_on_failure: A boolean flag to determine whether to perform teardown operations if any failure occurs during the method execution. Default value is `True`.
        :param fail_early: A boolean flag to determine whether to abort the process as soon as a tool or module fails to initialize. Default value is `False`.
        :return: A boolean value indicating whether the tools and modules installation was successful. Returns `True` if both tools and modules were installed successfully, otherwise returns `False`.
        """
        tools_installed = self.install_tools(teardown_on_failure, fail_early)
        modules_installed = self.install_modules(teardown_on_failure, fail_early)

        if not tools_installed:
            print("ERROR: Failed to install tools!", file=sys.stderr)
        if not modules_installed:
            print("ERROR: Failed to install modules!", file=sys.stderr)

        return tools_installed and modules_installed

    def install_tools(self, teardown_on_failure=True, fail_early=True):
        """
        Install tools layer by layer so that their dependencies are all met before being installed.

        :param teardown_on_failure: If True, rollback other tools if any tool installation fails.
        :type teardown_on_failure: bool
        :param fail_early: If True, function will return false as soon as a tool fails to initialize.
        :type fail_early: bool
        :return: True if all tools are installed successfully, False otherwise.
        :rtype: bool
        """

        # Early exit if there are no tools to install.
        if len(self.tools) == 0:
            print("Nothing to do.")
            return False

        print("Installing tools...")

        failed_tools = []
        successful_tools = []
        for layer in self.tool_dependencies:
            # Install tools layer by layer so that their dependencies are all met before being installed
            early_exit = False

            for tool in (tool for tool in self.tools if tool.name in layer):
                # Use the tool's check function to prevent attempts to install an existing tool
                if tool.check():
                    print(f".. Tool '{tool.name}' is already installed, skipping.")
                    continue

                # Initialize this tool, adding it to the list of failures if it cannot be initialized
                if not tool.initialize():
                    failed_tools.append(tool.name)
                    if fail_early:
                        early_exit = True
                else:
                    successful_tools.append(tool.name)

            if early_exit:
                break

        # Upon any failed tools, report which tools failed...
        if len(failed_tools) > 0:
            print("Failed tools:", failed_tools, file=sys.stderr)

            # ... and teardown if specified
            if teardown_on_failure:
                print("Rolling back successfully installed tools:", successful_tools, file=sys.stderr)

                destroyed_tools = []
                for tool in [tool for tool in self.tools if tool.name in successful_tools]:
                    if not tool.destroy():
                        # TODO handle failure to destroy better
                        print(f"FATAL: Failed to destroy tool \"{tool.name}\"", file=sys.stderr)
                        print(f".. Only destroyed these tools: {destroyed_tools}", file=sys.stderr)
                        sys.exit(1)
                    else:
                        destroyed_tools.append(tool.name)

            # If any tools failed
            return False

        # If all tools were successfully installed or were already installed
        return True

    def install_modules(self, teardown_on_failure=True, fail_early=True):
        """
        Install modules layer by layer so that their dependencies are all met before being installed.

        :param teardown_on_failure: If True, rollback other tools if any module installation fails.
        :type teardown_on_failure: bool
        :param fail_early: If True, function will return false as soon as a tool fails to initialize.
        :type fail_early: bool
        :return: True if all modules are installed successfully, False otherwise.
        :rtype: bool
        """

        # Early exit if there are no modules to install.
        if len(self.modules) == 0:
            print("Nothing to do.")
            return False

        print("Installing modules...")

        failed_modules = []
        successful_modules = []
        for layer in self.module_dependencies:
            # Install modules layer by layer so that their dependencies are all met before being installed
            early_exit = False

            for module in (module for module in self.modules if module.name in layer):
                # Initialize this module, adding it to the list of failures if it cannot be initialized
                if not module.initialize():
                    failed_modules.append(module.name)
                    if fail_early:
                        early_exit = True
                else:
                    successful_modules.append(module.name)

            if early_exit:
                break

        # Report any failed modules
        if len(failed_modules) > 0:
            print("Failed modules:", failed_modules, file=sys.stderr)

            # Destroy modules which were successfully installed if specified
            if teardown_on_failure:
                print("Rolling back successfully installed modules:",
                      successful_modules,
                      file=sys.stderr)

                destroyed_modules = []
                for module in [module for module in self.modules if module.name in successful_modules]:
                    if not module.destroy():
                        # TODO handle failure to destroy better
                        print(f"FATAL: Failed to destroy module \"{module.name}\"", file=sys.stderr)
                        print(f".. Only destroyed these modules: {destroyed_modules}", file=sys.stderr)
                        sys.exit(1)
                    else:
                        destroyed_modules.append(module.name)

            # If any modules failed to initialize
            return False

        # If all modules were successfully initialized
        return True

    def get_init_options(self):
        """
        Returns a list of tuples containing the name and init_options of modules
        that have a non-null value for init_options in the self.modules list.

        :return: A list of tuples where each tuple contains the name and init_options
                 of modules satisfying the condition.
        """
        return [(module.name, module.init_options) for module in self.modules if module.init_options is not None]

    def set_init_options(self, options):
        """
        Sets the init options of the Starter to be used before calling .up()

        :param options: A dictionary of module and option names along with their corresponding values.
                        Example: {("react", "MODULE_REACT_USE_TYPESCRIPT"): True,
                                  ("react", "MODULE_REACT_APP_NAME"): "example-react-app"}
        :return: None
        """
        for module_name, option_name in options:
            # Get the value from the options set
            value = options[(module_name, option_name)]

            # Update the environment
            os.environ[option_name] = str(value)

            # Update the internal variable of the option itself
            module = [module for module in self.modules if module.name == module_name][0]
            option = [option for option in module.init_options if option.name == option_name][0]
            option.value = value

        pass


def create_dependency_layers(items: list[Module or Tool]) -> list[list[str]]:
    """
    Generate dependency layers based on the given items such that each inner list's dependencies are all contained
    within the preceding inner list (the first inner list has no dependencies).

    :param items: a list of `Module` or `Tool` objects representing the items
    :type items: list[Module or Tool]
    :return: a list of lists, each containing item names grouped by their dependencies
    :rtype: list[list[str]]
    """
    # Handle dependencies
    dependency_layers = [[item.name for item in items if item.dependencies is None]]

    # Check for any unfulfilled dependencies,
    #  collect all items that are in any item's depends_on fields
    all_items_depended_upon = set(
        itertools.chain.from_iterable([item.dependencies for item in items if item.dependencies is not None]))

    # Check if any items that are depended upon are not present (e.g. 'a' requires 'z' but only 'a' and 'b' are defined)
    unmet_dependencies = all_items_depended_upon - set([item.name for item in items])

    if len(unmet_dependencies) > 0:
        print(f"ERROR: Dependency not met {unmet_dependencies}", file=sys.stderr)
        exit(1)

    # Modules with no dependencies are added to the first layer

    # Put remaining modules (those with dependencies) in a set
    dependent_items = False
    if len(dependency_layers) > 0:
        dependent_items = set([item for item in items if item.name not in dependency_layers[0]])

    # Add items to layers until none are left
    while dependent_items:
        scheduled_items = list(itertools.chain.from_iterable(dependency_layers))

        added_items = []
        for dependent_item in dependent_items:
            if all(needed in scheduled_items for needed in dependent_item.dependencies):
                added_items.append(dependent_item)

        if len(added_items) == 0:
            print(f"ERROR: Could not meet dependencies for {[item.name for item in dependent_items]}, "
                  f"may be a circular dependency.", file=sys.stderr)
            exit(1)

        for added_item in added_items:
            dependent_items.remove(added_item)

        dependency_layers.append([item.name for item in added_items])

    return dependency_layers


def parse_starterfile(starterfile_stream: TextIO) -> Starter:
    """
    Parse a Starterfile.yaml

    Checks the Starterfile, Modules, Tools, and their constituent dependencies against their respective schemas and
    creates a `Starter` complete with dependency ordering for tools and modules.

    :param starterfile_stream: The stream representing the starter file.
    :type starterfile_stream: TextIO
    :return: The parsed Starter object.
    :rtype: Starter
    """
    loaded = yaml.safe_load(starterfile_stream)
    Starter.starterfile_schema.validate(loaded)

    for env_file in loaded["env_file"]:
        _path = os.path.join(os.path.dirname(starterfile_stream.name), env_file)
        load_dotenv(str(_path))

    tools = []

    for tool_name in loaded["tools"]:
        _tool = loaded["tools"][tool_name]
        tool = Tool.tool_schema.validate(_tool)

        dependencies = tool["depends_on"] if "depends_on" in _tool else None

        if type(dependencies) is str:
            dependencies = [dependencies]

        tools.append(Tool(tool_name, dependencies, tool["scripts"]))

    tool_dependencies = create_dependency_layers(tools)

    print("SUCCESS! Parsed tools:", [tool.name for tool in tools])

    modules = []

    for module_name in loaded["modules"]:
        _module = loaded["modules"][module_name]
        module = Module.module_schema.validate(_module)

        modules.append(create_module(module, module_name))

    module_dependencies = create_dependency_layers(modules)

    print("SUCCESS! Parsed modules:", [module.name for module in modules])

    return Starter(
        modules=modules,
        tools=tools,
        module_dependencies=module_dependencies,
        tool_dependencies=tool_dependencies
    )


if __name__ == "__main__":
    with open("../Starterfile.yaml", "r") as f:
        s = parse_starterfile(f)

    # for opt in s.get_init_options():
    #     response = cli_prompt(opt)
    #     os.environ(opt.env_name) = response

    stuff = s.get_init_options()

    example = {
        ("react", "MODULE_REACT_USE_TYPESCRIPT"): True,
        ("react", "MODULE_REACT_APP_NAME"): "example-react-app"
    }

    s.set_init_options(example)
    s.up()
