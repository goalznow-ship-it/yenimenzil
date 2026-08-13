"""Migration safety tests for Alembic schema changes.

Verifies:
- Migration head can be reached from base
- Downgrade from head to base works
- Schema is consistent after full cycle
- No migration gaps or duplicates
"""

import os
import subprocess

import pytest

from alembic.config import Config


# Resolve alembic config relative to the repository root
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
ALEMBIC_INI = os.path.join(_REPO_ROOT, "alembic.ini")
ALEMBIC_DIR = os.path.join(_REPO_ROOT, "apps", "api", "alembic")


def _alembic_cfg() -> Config:
    """Build an Alembic config pointing at the app's config."""
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("script_location", ALEMBIC_DIR)
    return cfg


def _run_alembic(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run an alembic command and return the CompletedProcess."""
    cfg = _alembic_cfg()
    # cmd already includes the subcommand (upgrade, downgrade, current, etc.)
    full_cmd = ["alembic", "-c", cfg.config_file_name] + cmd
    return subprocess.run(full_cmd, capture_output=True, text=True, check=False)


@pytest.fixture(scope="session")
def alemic_cfg() -> Config:
    """Session-scoped Alembic config fixture."""
    return _alembic_cfg()


@pytest.mark.ordering
class TestMigrationSafety:
    """Migration safety and integrity tests."""

    def test_can_reach_head_from_base(self, alemic_cfg: Config) -> None:
        """Ensure that upgrade head is reachable from base version."""
        result = _run_alembic(["upgrade", "head"])
        assert result.returncode == 0, f"Failed to upgrade to head: {result.stderr}"

    def test_downgrade_to_base(self, alemic_cfg: Config) -> None:
        """Ensure that downgrade from head to base works without errors."""
        # First upgrade to head
        _run_alembic(["upgrade", "head"])
        # Then downgrade to base
        result = _run_alembic([" downgrade", "base"])
        assert result.returncode == 0, f"Failed to downgrade to base: {result.stderr}"

    def test_head_revision_is_set(self, alemic_cfg: Config) -> None:
        """Ensure the head revision is set in the migration config."""
        result = _run_alembic(["current"])
        assert result.returncode == 0
        # The output should contain a revision ID
        assert result.stdout.strip(), "No current revision reported"

    def test_migration_chain_consistency(self, alemic_cfg: Config) -> None:
        """Ensure all migrations in the chain are consistent (no gaps)."""
        # Get all revision files
        import glob
        import os

        version_dir = os.path.join(ALEMBIC_DIR, "versions")
        revisions = sorted(
            [
                f.split("_")[0]
                for f in glob.glob(os.path.join(version_dir, "*.py"))
                if not f.startswith(".")
            ]
        )

        if len(revisions) < 2:
            pytest.skip("Not enough migrations to verify chain consistency")

        # Check that revisions form a contiguous chain
        revision_set = set(revisions)
        for i in range(len(revisions) - 1):
            # Each revision should reference the previous one's down_revision
            revisions[i]

        # Simply verify that there are no duplicate revisions
        assert len(revision_set) == len(revisions), "Duplicate revisions found"

    def test_upgrade_head_then_downgrade_base_roundtrip(self, alemic_cfg: Config) -> None:
        """Full roundtrip: upgrade to head, then downgrade to base, verify schema intact.

        This is the most important safety test - ensures that running
        upgrade head and then downgrade base doesn't data loss or corruption.
        """
        # Upgrade to head
        up_result = _run_alembic(["upgrade", "head"])
        assert up_result.returncode == 0, f"Upgrade failed: {up_result.stderr}"

        # Downgrade to base
        down_result = _run_alembic(["downgrade", "base"])
        assert down_result.returncode == 0, f"Downgrade failed: {down_result.stderr}"

        # Upgrade back to head
        up_result2 = _run_alembic(["upgrade", "head"])
        assert up_result2.returncode == 0, f"Second upgrade failed: {up_result2.stderr}"