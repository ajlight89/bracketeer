"""Smoke tests: prove the package is installed and importable.

If these fail, nothing else in the test suite can pass.
"""

import re
from importlib.metadata import version

import bracketeer


def test_package_imports_with_docstring():
    assert bracketeer.__doc__ is not None


def test_installed_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", version("bracketeer"))
