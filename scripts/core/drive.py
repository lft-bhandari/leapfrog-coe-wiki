from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import markdownify
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
# Google Docs HTML export; text/plain loses headings and lists
_EXPORT_MIME = "text/html"

_PATH_ID_RE = re.compile(r"/d/([a-zA-Z0-9_-]+)")
_QUERY_ID_RE = re.compile(r"[?&]id=([a-zA-Z0-9_-]+)")


def extract_file_id(url_or_id: str) -> str:
    """Extract a Drive file ID from a Google Docs/Drive URL or return the ID unchanged.

    Handles both the current path format (/d/<id>) and the older sharing
    format (?id=<id>). Raises ValueError for drive.google.com URLs that
    match neither pattern, rather than silently passing an invalid ID.

    Args:
        url_or_id: A full Google Docs/Drive URL or a bare Drive file ID.

    Returns:
        The file ID string.

    Raises:
        ValueError: If the argument looks like a Drive URL but no file ID can be extracted.
    """
    match = _PATH_ID_RE.search(url_or_id) or _QUERY_ID_RE.search(url_or_id)
    if match:
        return match.group(1)
    # If it contains a Drive domain but matched nothing, the format is unrecognised
    if "google.com" in url_or_id:
        raise ValueError(
            f"Could not extract a file ID from URL: {url_or_id!r}. "
            "Expected a /d/<id> path or ?id=<id> query parameter."
        )
    # Plain string with no URL — treat as a bare file ID
    return url_or_id


def is_drive_url(arg: str) -> bool:
    """Return True if the argument looks like a Google Drive or Docs URL.

    Args:
        arg: CLI argument string.

    Returns:
        True for docs.google.com or drive.google.com URLs.
    """
    return "docs.google.com" in arg or "drive.google.com" in arg


def fetch_doc_as_markdown(file_id: str, service: Any) -> tuple[str, str]:
    """Fetch a Google Doc and return its title and markdown content.

    Exports the document as HTML then converts to markdown to preserve
    headings and list structure that plain-text export loses.

    Args:
        file_id: Google Drive file ID.
        service: Authenticated Google Drive API service resource.

    Returns:
        Tuple of (title, markdown_content).

    Raises:
        googleapiclient.errors.HttpError: If the file is not found or inaccessible.
    """
    metadata = service.files().get(fileId=file_id, fields="name").execute()
    title: str = metadata["name"]

    html_bytes: bytes = service.files().export_media(
        fileId=file_id, mimeType=_EXPORT_MIME
    ).execute()
    html = html_bytes.decode("utf-8")

    markdown = markdownify.markdownify(html, heading_style="ATX")
    return title, markdown


def build_drive_service(credentials_path: Path, token_cache_path: Path) -> Any:
    """Build an authenticated Google Drive API service, running OAuth if needed.

    On first run, opens a browser for the user to authorise access and caches
    the resulting token. Subsequent calls load the cached token silently.

    Args:
        credentials_path: Path to the OAuth client credentials JSON file
            downloaded from Google Cloud Console.
        token_cache_path: Path where the user token will be cached after auth.

    Returns:
        Authenticated Drive API service resource.
    """
    creds: Credentials | None = None
    if token_cache_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_cache_path), _SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), _SCOPES
            )
            # run_local_server opens a browser tab for the OAuth consent screen
            creds = flow.run_local_server(port=0)
        token_cache_path.parent.mkdir(parents=True, exist_ok=True)
        token_cache_path.write_text(creds.to_json())

    return build("drive", "v3", credentials=creds)
