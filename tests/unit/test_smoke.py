"""Smoke tests: the package is installed, importable and correctly packaged.

If these fail, the problem is the environment or the packaging, not the domain code.
"""

import re

import bracketeer


def test_version_comes_from_installed_metadata() -> None:
    # "+unknown" means the package was imported from source without being installed.
    assert "+unknown" not in bracketeer.__version__
    assert re.fullmatch(r"\d+\.\d+\.\d+\S*", bracketeer.__version__)


def test_package_is_regular_not_namespace() -> None:
    # Regression test: a missing or misplaced src/bracketeer/__init__.py turns the folder
    # into an implicit namespace package (PEP 420). It still imports, but it is empty
    # and has no __file__.
    assert bracketeer.__file__ is not None
    assert bracketeer.__file__.endswith("__init__.py")
