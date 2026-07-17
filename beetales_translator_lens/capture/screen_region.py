"""Qt-independent model for virtual desktop regions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScreenRegion:
    """Rectangle in physical virtual-desktop coordinates."""

    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def is_valid(self) -> bool:
        return self.width >= 16 and self.height >= 16

    def as_mss_monitor(self) -> dict[str, int]:
        return {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
        }

    def intersection(self, bounds: "ScreenRegion") -> "ScreenRegion | None":
        left = max(self.left, bounds.left)
        top = max(self.top, bounds.top)
        right = min(self.right, bounds.right)
        bottom = min(self.bottom, bounds.bottom)
        if right - left < 16 or bottom - top < 16:
            return None
        return ScreenRegion(left, top, right - left, bottom - top)

    @classmethod
    def from_mapping(cls, value: dict[str, int]) -> "ScreenRegion":
        """Accept both MSS keys and Qt geometry keys."""

        return cls(
            left=int(value.get("left", value.get("x", 0))),
            top=int(value.get("top", value.get("y", 0))),
            width=int(value["width"]),
            height=int(value["height"]),
        )
