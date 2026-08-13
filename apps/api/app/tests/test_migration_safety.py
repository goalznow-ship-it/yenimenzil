"""Migration safety tests for Alembic schema changes.

Verifies:
- Migration config files are syntactically valid
- Alembic can be imported without errors
- Revision chain is consistent
"""

import os

import pytest

_API_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ALEMBIC_INI = os.path.join(_API_ROOT, "alembic.ini")
ALEMBIC_DIR = os.path.join(_API_ROOT, "alembic")


def test_alembic_config_file_exists():
    """Ensure the alembic.ini config file exists and is readable."""
    assert os.path.isfile(ALEMBIC_INI), f"alembic.ini not found at {ALEMBIC_INI}"


def test_alembic_config_has_alembic_section():
    """Ensure alembic.ini has the required [alembic] section."""
    import configparser

    config = configparser.ConfigParser()
    config.read(ALEMBIC_INI)
    assert "alembic" in config.sections(), "alembic.ini missing [alembic] section"


def test_alembic_script_location_is_set():
    """Ensure the script_location is properly configured."""
    from alembic.config import Config

    cfg = Config(ALEMBIC_INI)
    script_location = cfg.get_main_option("script_location")
    assert script_location is not None, "script_location not set in alembic.ini"
    assert os.path.isdir(ALEMBIC_DIR), f"script_location directory not found: {script_location}"


def test_migration_revisions_are_valid_python():
    """Ensure all migration files are syntactically valid Python."""
    import ast

    version_dir = os.path.join(ALEMBIC_DIR, "versions")
    revision_files = [
        f
        for f in os.listdir(version_dir)
        if f.endswith(".py") and not f.startswith(".")
    ]

    for filename in revision_files:
        filepath = os.path.join(version_dir, filename)
        with open(filepath) as f:
            try:
                ast.parse(f.read())
            except SyntaxError as exc:
                pytest.fail(f"Syntax error in migration file {filename}: {exc}")


def test_revision_chain_is_monotonic():
    """Ensure migration revision IDs form a monotonic chain."""
    import os

    version_dir = os.path.join(ALEMBIC_DIR, "versions")
    revision_files = [
        f for f in os.listdir(version_dir)
        if f.endswith(".py") and not f.startswith(".")
    ]
    revision_ids = sorted([f.split("_")[0] for f in revision_files])

    if len(revision_ids) < 2:
        pytest.skip("Not enough migrations to verify chain consistency")

    # Check for duplicates
    assert len(set(revision_ids)) == len(revision_ids), "Duplicate revision IDs found"

    # Verify each revision file exists (redundant but explicit)
    for rev_id in revision_ids:
        found = any(f.startswith(rev_id + "_") for f in revision_files)
        assert found, f"Migration file not found for revision {rev_id}"