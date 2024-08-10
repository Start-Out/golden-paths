import pytest

from startout import starterfile


class Module:
    def __init__(self, name, dependencies):
        self.name = name
        self.dependencies = dependencies


class Tool:
    def __init__(self, name, dependencies):
        self.name = name
        self.dependencies = dependencies


@pytest.fixture
def no_dependency_modules():
   """Fixture to create list of `Module` objects with no dependencies."""
   return [Module(f"Module_{i}", None) for i in range(5)]


@pytest.fixture
def with_dependency_modules():
   """Fixture to create list of `Module`, `Tool` objects with dependencies."""
   return [Module("Module_0", None), Tool("Tool_1", ["Module_0"]), Module("Module_2", ["Tool_1"]),
           Tool("Tool_3", ["Module_2"]), Module("Module_4", ["Tool_3"])]


def test_create_dependency_layers_without_dependencies(no_dependency_modules):
    """Tests create_dependency_layers function with no module having any dependency."""
    layers = starterfile.create_dependency_layers(no_dependency_modules)
    assert len(layers) == 1
    assert all([isinstance(layer, str) for layer in layers[0]])


def test_create_dependency_layers_with_dependencies(with_dependency_modules):
    """Tests create_dependency_layers function with modules having dependencies."""
    layers = starterfile.create_dependency_layers(with_dependency_modules)
    assert len(layers) == 5
    assert all([isinstance(layer[0], str) for layer in layers])


def test_create_dependency_layers_with_missing_dependency():
    """Tests create_dependency_layers function with a missing dependency."""
    with pytest.raises(SystemExit) as e:
        modules = [Module(f"Module_{i}", [f"Module_{i - 1}"]) for i in range(1, 5)]
        modules.append(Module("Module_0", ["Module_5"]))  # Module_5 does not exist
        starterfile.create_dependency_layers(modules)
    assert str(e.value) == "1"


def test_create_dependency_layers_with_circular_dependency():
    """Tests create_dependency_layers function with a circular dependency."""
    with pytest.raises(SystemExit) as e:
        modules = [Module(f"Module_{i}", [f"Module_{(i + 1) % 5}"]) for i in range(5)]
        starterfile.create_dependency_layers(modules)
    assert str(e.value) == "1"