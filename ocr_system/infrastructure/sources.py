"""
Image Source adapters.

LocalFileImageSource — read images from filesystem.
HttpImageSource — fetch images via HTTP.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import aiohttp

from ..application import ImageSource
from ..domain import (
    BoundingBox,
    Document,
    DocumentType,
    TextLine,
    Paragraph,
    Table,
    Entity,
    OCRPath,
)


class LocalFileImageSource(ImageSource):
    """Adapter for reading images from local filesystem."""

    def __init__(self, base_path: str):
        super().__init__()
        self.base_path = Path(base_path)

    async def get_image(self, image_url: str) -> bytes:
        """Get image data from local file."""
        if image_url.startswith("file://"):
            image_url = image_url[7:]

        path = Path(image_url)
        if not path.is_absolute():
            path = self.base_path / path

        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        return await asyncio.to_thread(path.read_bytes)

    async def exists(self, image_url: str) -> bool:
        """Check if image exists."""
        try:
            path = Path(image_url)
            if not path.is_absolute():
                path = self.base_path / path
            return path.exists()
        except Exception:
            return False


class HttpImageSource(ImageSource):
    """Adapter for fetching images via HTTP."""

    def __init__(self, timeout_seconds: float = 30.0):
        super().__init__()
        self.timeout = timeout_seconds

    async def get_image(self, image_url: str) -> bytes:
        """Fetch image from HTTP URL."""
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            async with session.get(image_url) as response:
                response.raise_for_status()
                return await response.read()

    async def exists(self, image_url: str) -> bool:
        """Check if URL exists (HEAD request)."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5.0)
            ) as session:
                async with session.head(image_url) as response:
                    return response.status == 200
        except Exception:
            return False
