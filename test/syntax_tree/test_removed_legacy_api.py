import importlib

import pytest


def test_legacy_type_module_is_removed():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("renaissance.integrations.types")
