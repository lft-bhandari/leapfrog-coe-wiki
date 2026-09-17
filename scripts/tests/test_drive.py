import pytest
from unittest.mock import MagicMock
from core.drive import (
    extract_file_id,
    fetch_doc_as_markdown,
    is_drive_url,
)

# --- Slice 1: URL parsing ---

def test_extract_file_id_from_full_url():
    url = "https://docs.google.com/document/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ/edit"
    assert extract_file_id(url) == "1aBcDeFgHiJkLmNoPqRsTuVwXyZ"


def test_extract_file_id_returns_bare_id_unchanged():
    assert extract_file_id("1aBcDeFgHiJkLmNoPqRsTuVwXyZ") == "1aBcDeFgHiJkLmNoPqRsTuVwXyZ"


def test_extract_file_id_from_sharing_url():
    url = "https://docs.google.com/document/d/ABC123_xyz-456/view?usp=sharing"
    assert extract_file_id(url) == "ABC123_xyz-456"


def test_extract_file_id_from_old_style_query_param():
    url = "https://drive.google.com/open?id=1aBcDeFgHiJkLmNoPqRsTuVwXyZ"
    assert extract_file_id(url) == "1aBcDeFgHiJkLmNoPqRsTuVwXyZ"


def test_extract_file_id_raises_for_unrecognised_google_url():
    with pytest.raises(ValueError, match="Could not extract a file ID"):
        extract_file_id("https://google.com/unknown/path")


# --- Slice 2: URL detection ---

def test_is_drive_url_true_for_docs_google_com():
    assert is_drive_url("https://docs.google.com/document/d/abc/edit")


def test_is_drive_url_true_for_drive_google_com():
    assert is_drive_url("https://drive.google.com/file/d/abc/view")


def test_is_drive_url_false_for_local_path():
    assert not is_drive_url("/home/user/doc.md")


def test_is_drive_url_false_for_bare_id():
    assert not is_drive_url("1aBcDeFgHiJkLmNoPqRsTuVwXyZ")


# --- Slice 3: fetch_doc_as_markdown with mock client ---

def test_fetch_doc_as_markdown_returns_title_and_markdown():
    mock_service = MagicMock()
    # Simulate Drive files().get() returning metadata
    mock_service.files().get().execute.return_value = {"name": "My Research Doc"}
    # Simulate Drive files().export_media() returning HTML bytes
    mock_service.files().export_media.return_value = MagicMock(
        execute=MagicMock(return_value=b"<h1>Title</h1><p>Some content.</p>")
    )

    title, markdown = fetch_doc_as_markdown("FILE_ID", mock_service)

    assert title == "My Research Doc"
    assert "Title" in markdown
    assert "Some content." in markdown


def test_fetch_doc_as_markdown_converts_html_formatting():
    mock_service = MagicMock()
    mock_service.files().get().execute.return_value = {"name": "Doc"}
    mock_service.files().export_media.return_value = MagicMock(
        execute=MagicMock(return_value=b"<h2>Section</h2><ul><li>Item A</li><li>Item B</li></ul>")
    )

    _, markdown = fetch_doc_as_markdown("FILE_ID", mock_service)

    assert "## Section" in markdown
    assert "Item A" in markdown
