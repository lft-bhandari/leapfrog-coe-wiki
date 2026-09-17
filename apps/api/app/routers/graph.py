from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter

from app.services.graph_service import GraphData, build_graph

router = APIRouter(prefix="/api", tags=["graph"])

# WIKI_DIR env var lets deployments point at any wiki location without code changes.
# Falls back to the repo-relative path for local development.
_WIKI_DIR = Path(os.environ.get("WIKI_DIR", Path(__file__).parent.parent.parent.parent.parent / "wiki"))


@router.get("/graph", response_model=GraphData)
def get_graph() -> GraphData:
    """Return the wiki knowledge graph as nodes and edges for React Flow.

    Scans the wiki directory on each request. All 9 domain nodes are always
    present even if no pages have been ingested yet.
    """
    return build_graph(_WIKI_DIR)
