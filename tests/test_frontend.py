"""Regression tests for the native Document Sender panel bundle."""

from __future__ import annotations

from pathlib import Path

INTEGRATION_ROOT = Path(__file__).parents[1] / "custom_components" / "document_sender"


def test_panel_uses_local_lit_bundle() -> None:
    """Ensure the panel never relies on unsupported Home Assistant globals."""
    source = (
        INTEGRATION_ROOT / "frontend_src" / "document-sender-panel.js"
    ).read_text(encoding="utf-8")
    output = (
        INTEGRATION_ROOT / "frontend" / "document-sender-panel.js"
    ).read_text(encoding="utf-8")
    lit_bundle = INTEGRATION_ROOT / "frontend" / "lit-core.min.js"

    assert output == source
    assert 'from "./lit-core.min.js"' in output
    assert "window.LitElement" not in output
    assert 'customElements.define("document-sender-panel"' in output
    assert lit_bundle.stat().st_size > 10_000
