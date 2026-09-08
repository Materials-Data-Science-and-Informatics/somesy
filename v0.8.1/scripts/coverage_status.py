"""Mkdocs hook to run tests with coverage collection and generate a badge."""

import logging
from io import StringIO
from pathlib import Path

import anybadge
import pytest
from coverage import Coverage
from coverage.exceptions import NoSource
from interrogate import badge_gen
from interrogate.coverage import InterrogateCoverage

log = logging.getLogger("mkdocs")


badge_colors = {
    20: "red",
    40: "orange",
    60: "yellow",
    80: "greenyellow",
    90: "green",
}
"""Colors for overall coverage percentage (0-100)."""


def on_pre_build(config):
    """Generate coverage report if it is missing and create a badge."""
    if not Path("htmlcov").is_dir() or not Path(".coverage").is_file():
        log.info("Missing htmlcov or .coverage, running pytest to collect.")
        pytest.main(["--cov", "--cov-report=html"])
    else:
        log.info("Using existing coverage data.")

    cov_percent = 0
    try:
        cov_percent = get_coverage_percentage()
    except NoSource:
        # Source file is either deleted or moved, so we can't generate a badge, rerun the tests
        log.info("Change in the source files, running pytest to collect.")
        pytest.main(["--cov", "--cov-report=html"])
        cov_percent = get_coverage_percentage()

    badge = anybadge.Badge(
        "coverage",
        cov_percent,
        value_prefix=" ",
        value_suffix="% ",
        thresholds=badge_colors,
    )

    badge_svg = Path("docs/coverage_badge.svg")
    if badge_svg.is_file():
        badge_svg.unlink()
    badge.write_badge(badge_svg)

    # generates a docs coverage badge in docs/interrogate_badge.svg
    doc_cov = InterrogateCoverage(paths=["src"]).get_coverage()
    log.info(f"Docs Coverage: {doc_cov.perc_covered}%, generating badge.")
    badge_gen.create("docs", doc_cov)


def get_coverage_percentage():
    """Return the coverage percentage from the .coverage file."""
    cov = Coverage()
    cov.load()
    cov_percent = int(cov.report(file=StringIO()))
    log.info(f"Test Coverage: {cov_percent}%, generating badge.")

    return cov_percent
