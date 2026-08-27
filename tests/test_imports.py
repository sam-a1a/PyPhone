"""Import smoke tests.

The pygame screens are drawing code and are not unit tested, but a module that
does not even import is worth catching, so every one of them is imported here
under a headless SDL driver.
"""
import importlib
import pkgutil

import pytest

MODULES = [
    "config",
    "utils",
    "main",
    "components",
    "components.dock",
    "components.icons",
    "components.status_bar",
    "components.widgets",
    "apps",
    "apps.app_manager",
    "apps.base_app",
    "apps.splash_screen",
    "apps.shared",
    "apps.shared.database",
    "apps.shared.models",
    "apps.shared.security",
    "apps.shared.validators",
    "apps.health",
    "apps.health.health_app",
    "apps.health_admin",
    "apps.health_admin.health_admin_app",
]


@pytest.mark.parametrize("name", MODULES)
def test_module_imports(name):
    assert importlib.import_module(name) is not None


def _submodules(package_name):
    package = importlib.import_module(package_name)
    return [f"{package_name}.{m.name}" for m in pkgutil.iter_modules(package.__path__)]


@pytest.mark.parametrize("package", [
    "apps.health.screens",
    "apps.health.components",
    "apps.health_admin.screens",
    "apps.health_admin.components",
])
def test_every_screen_and_component_imports(package):
    names = _submodules(package)
    assert names, f"no modules found under {package}"
    for name in names:
        importlib.import_module(name)


def test_pygame_runs_headless():
    # If this fails, the whole suite is about to fail for the same reason
    import pygame
    pygame.display.init()
    assert pygame.display.get_init() is True
    assert pygame.display.set_mode((64, 64)).get_size() == (64, 64)
