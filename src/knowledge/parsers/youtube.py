"""
YouTube transcript parser stub.
TODO: Implement using youtube-transcript-api.
"""

import structlog

logger = structlog.get_logger()


class YoutubeParser:
    """Extract transcripts from YouTube videos."""

    async def parse(self, video_url: str) -> str | None:
        """
        Fetch and return the transcript for a YouTube video.
        Falls back to auto-generated captions if manual not available.
        """
        logger.info("youtube_parser_stub", url=video_url)
        # TODO: Implement with youtube-transcript-api
        return None
