"""OCR text cleanup that preserves Unicode and chat message structure."""

from __future__ import annotations

import re

SPACES = re.compile(r"[ \t\f\v]+")
MEANINGFUL = re.compile(r"[\w\u3040-\u30ff\u3400-\u9fff]", re.UNICODE)
MESSAGE_PREFIX = re.compile(
    r"^(?P<prefix>(?:\[[^\]\n]{1,40}\]|<[^>\n]{1,40}>|[\w .'-]{1,40}:|[\w .'-]{1,40}\s+—)\s*)(?P<body>.+)$",
    re.UNICODE,
)


def normalize_ocr_text(text: str) -> str:
    """Normalize spacing while retaining case, accents, and message breaks."""

    normalized_lines: list[str] = []
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = SPACES.sub(" ", raw_line).strip()
        if not line or not MEANINGFUL.search(line):
            continue
        normalized_lines.append(line)
    return "\n".join(normalized_lines)


def split_message_prefix(line: str) -> tuple[str, str]:
    """Return a likely username prefix and the translatable message body."""

    match = MESSAGE_PREFIX.match(line)
    if not match:
        return "", line
    return match.group("prefix"), match.group("body")
