"""Architecture tests: enforce the dependency rule (NFR-MA-1).

These tests read the source code without running it. They parse each module
with the ast module and check what it imports.
"""

import ast
from pathlib import Path

import pytest

import bracketeer

PACKAGE_DIR = Path(bracketeer.__file__).parent
RELATIVE = "<relative import>"

# The domain may import only these (an allow-list). Anything else, such as
# os, time, sqlite3, tkinter, or jinja2, fails until it's reviewed and added.
DOMAIN_ALLOWED = {
    "__future__",
    "abc",
    "collections",
    "dataclasses",
    "enum",
    "functools",
    "itertools",
    "math",
    "random",
    "typing",
    "bracketeer.domain",
}

# Lower layers must never import the layers above them (a deny-list).
UPPER_LAYERS = {"bracketeer.app", "bracketeer.ui"}


def modules_in(layer):
    """Return every .py file in a layer folder, such as 'domain'."""
    folder = PACKAGE_DIR / layer
    if not folder.is_dir():
        return []
    return sorted(folder.rglob("*.py"))


def imports_in(path):
    """Return the full name of every module a file imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.add(RELATIVE if node.level > 0 else node.module)
    return names


def is_within(name, packages):
    """Return True if name is one of the packages or inside one of them."""
    return any(name == p or name.startswith(p + ".") for p in packages)


def short_name(path):
    return path.relative_to(PACKAGE_DIR).as_posix()


DOMAIN_FILES = modules_in("domain")
LOWER_FILES = modules_in("persistence") + modules_in("export")


def test_checker_finds_every_kind_of_import(tmp_path):
    sample = tmp_path / "sample.py"
    sample.write_text(
        "import sqlite3\nfrom jinja2 import Template\nfrom . import x\n",
        encoding="utf-8",
    )
    assert imports_in(sample) == {"sqlite3", "jinja2", RELATIVE}


def test_domain_has_modules_to_check():
    assert DOMAIN_FILES, f"No domain modules found under {PACKAGE_DIR}"


@pytest.mark.parametrize("path", DOMAIN_FILES, ids=short_name)
def test_domain_imports_only_allowed_modules(path):
    bad = {name for name in imports_in(path) if not is_within(name, DOMAIN_ALLOWED)}
    assert not bad, f"{short_name(path)} imports {sorted(bad)}"


@pytest.mark.parametrize("path", LOWER_FILES, ids=short_name)
def test_lower_layers_never_import_upper_layers(path):
    bad = {
        name
        for name in imports_in(path)
        if name == RELATIVE or is_within(name, UPPER_LAYERS)
    }
    assert not bad, f"{short_name(path)} imports {sorted(bad)}"
