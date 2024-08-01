from startout.util import replace_env, type_tool


class InitOption:
    """
    Initializes an instance of the `InitOption` class. This class is used as an API for setting options before a Module
    is initialized (e.g. name of the project, passwords, etc.).

    This API is meant to be used by tools which interface with the Starterfile parser, e.g. the Startout CLI.

    :param options_set: A dictionary containing the options for initialization.
                        The dictionary should have the following keys:
                        - "default" (required): The default value for the option.
                        - "type" (optional): The type of the option value.
                        - "env_name" (required): The name of the environment variable associated with the option.
                        - "prompt" (required): The prompt to display when prompting for the option value.
    """

    def __init__(self, options_set):
        """
        Initializes the method.

        :param options_set: A dictionary containing the options for the method.
                    - "default" (required): The default value for the option. This value may not be `None`
                    - "type" (optional): The type of the option value.
                    - "env_name" (required): The name of the environment variable associated with the option.
                    - "prompt" (required): The prompt to display when prompting for the option value.
        """
        default = options_set["default"]

        assert default is not None

        if "type" in options_set.keys():
            _t = type_tool(options_set["type"])
            default = _t(default)

        self.name = replace_env(options_set["env_name"])
        self.default = replace_env(default) if type(default) is str else default
        self.prompt = replace_env(options_set["prompt"])
        self.value = None
