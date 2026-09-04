"""End-to-end tests for the Somesy pre-commit hook."""

import shutil
import subprocess
import sys

import tomlkit


def test_precommit_sync_requires_staging_generated_metadata(
    tmp_path, create_files, file_types
):
    """Fail after syncing changed metadata, then pass once generated files are staged."""
    somesy = shutil.which("somesy")
    assert somesy, "The somesy command must be available to test its hook."

    create_files(
        {
            (file_types.SOMESY, "somesy.toml"),
            (file_types.POETRY, "pyproject.toml"),
        }
    )
    (tmp_path / ".pre-commit-config.yaml").write_text(
        "repos:\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: somesy\n"
        "        name: Run somesy sync\n"
        "        entry: somesy sync\n"
        "        language: system\n"
        "        files: ^somesy\\.toml$\n"
        "        pass_filenames: false\n"
    )

    def run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=tmp_path,
            check=check,
            text=True,
            capture_output=True,
        )

    run("git", "init", "-q")
    run("git", "config", "user.name", "Test User")
    run("git", "config", "user.email", "test@example.com")
    run("git", "config", "commit.gpgsign", "false")
    run(somesy, "sync")
    run("git", "add", ".")
    run("git", "commit", "-qm", "initial")
    run(sys.executable, "-m", "pre_commit", "install")

    input_file = tmp_path / "somesy.toml"
    content = tomlkit.parse(input_file.read_text())
    content["project"]["version"] = "2.0.0"
    input_file.write_text(tomlkit.dumps(content))
    run("git", "add", "somesy.toml")

    failed_hook = run(sys.executable, "-m", "pre_commit", "run", check=False)
    assert failed_hook.returncode == 1
    assert "Run somesy sync" in failed_hook.stdout
    assert "version: 2.0.0" in (tmp_path / "CITATION.cff").read_text(), (
        failed_hook.stdout + failed_hook.stderr
    )

    run("git", "add", ".")
    committed = run("git", "commit", "-m", "update metadata", check=False)
    assert committed.returncode == 0, committed.stderr
