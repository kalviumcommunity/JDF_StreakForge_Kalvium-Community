"""Headless checks: boots the app and visits every section, asserting no errors."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")
SECTIONS = ["Overview", "Trends", "Data Explorer", "Upload & Sync"]


def run(section=None):
    at = AppTest.from_file(APP, default_timeout=120).run()
    if section:
        at.sidebar.radio[0].set_value(section).run()
    return at


def test_app_starts():
    assert not run().exception


def test_sidebar_has_all_sections():
    assert run().sidebar.radio[0].options == SECTIONS


@pytest.mark.parametrize("section", SECTIONS)
def test_section_renders(section):
    at = run(section)
    assert not at.exception
    assert at.title[0].value


def test_overview_shows_five_kpis():
    at = run("Overview")
    assert len(at.metric) >= 5


def test_upload_section_shows_empty_state_before_any_upload():
    # AppTest cannot simulate a file upload, which is exactly why the parsing
    # and validation logic lives in upload_utils and is tested directly there.
    # What AppTest can prove is that the empty state renders without error.
    at = run("Upload & Sync")
    assert not at.exception
    assert any("No file loaded yet" in i.value for i in at.info)


def test_every_section_has_an_expander():
    for section in SECTIONS:
        assert len(run(section).expander) >= 1