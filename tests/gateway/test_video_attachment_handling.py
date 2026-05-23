"""Tests for inbound video attachment handling."""

from unittest.mock import patch

import pytest

from gateway.config import GatewayConfig, Platform
from gateway.platforms.base import MessageEvent, MessageType
from gateway.session import SessionSource


def _make_runner() -> "GatewayRunner":  # type: ignore[name-defined]
    from gateway.run import GatewayRunner

    runner = GatewayRunner.__new__(GatewayRunner)
    runner.config = GatewayConfig()
    runner.adapters = {}
    runner._model = "test-model"
    runner._base_url = ""
    runner._has_setup_skill = lambda: False
    return runner


def _source() -> SessionSource:
    return SessionSource(platform=Platform.MATRIX, chat_id="!room:example.org", chat_type="dm")


def _video_event(path: str = "/tmp/cache/videos/video_123456789abc_clip.mp4") -> MessageEvent:
    return MessageEvent(
        text="please inspect this",
        message_type=MessageType.VIDEO,
        source=_source(),
        media_urls=[path],
        media_types=["video/mp4"],
    )


@pytest.mark.asyncio
async def test_video_attachment_adds_agent_visible_path_note():
    runner = _make_runner()
    source = _source()
    event = _video_event()

    with patch(
        "tools.credential_files.to_agent_visible_cache_path",
        side_effect=lambda path: f"/agent{path}",
    ):
        result = await runner._prepare_inbound_message_text(
            event=event,
            source=source,
            history=[],
        )

    assert result is not None
    assert "video file attachment" in result.lower()
    assert "clip.mp4" in result
    assert "/agent/tmp/cache/videos/video_123456789abc_clip.mp4" in result
    assert "Use video_analyze with this path" in result
    assert "please inspect this" in result


def test_video_media_placeholder_names_video_attachment():
    from gateway.run import _build_media_placeholder

    event = _video_event("/tmp/cache/videos/video_123456789abc_clip.mp4")

    assert _build_media_placeholder(event) == (
        "[User sent a video: /tmp/cache/videos/video_123456789abc_clip.mp4]"
    )
