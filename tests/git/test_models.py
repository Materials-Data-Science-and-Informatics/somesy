"""Tests for Git metadata models."""

import pytest

from somesy.git.models import GitAuthor


def test_git_author_rejects_negative_commit_count():
    with pytest.raises(ValueError):
        GitAuthor(name="Jane Doe", commit_count=-1)
