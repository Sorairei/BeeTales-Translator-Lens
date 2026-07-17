"""Region, negative-coordinate, and virtual-boundary tests."""

from beetales_translator_lens.capture.screen_region import ScreenRegion


def test_mss_mapping_preserves_negative_coordinates() -> None:
    region = ScreenRegion(-1420, 120, 640, 360)

    assert region.as_mss_monitor() == {
        "left": -1420,
        "top": 120,
        "width": 640,
        "height": 360,
    }


def test_intersection_clips_region_at_virtual_desktop_edge() -> None:
    desktop = ScreenRegion(-1920, 0, 3840, 1080)
    requested = ScreenRegion(-2000, 100, 300, 200)

    assert requested.intersection(desktop) == ScreenRegion(-1920, 100, 220, 200)


def test_intersection_rejects_region_outside_desktop() -> None:
    desktop = ScreenRegion(0, 0, 1920, 1080)

    assert ScreenRegion(-500, 20, 200, 100).intersection(desktop) is None


def test_minimum_region_is_enforced() -> None:
    assert ScreenRegion(0, 0, 15, 200).is_valid is False
    assert ScreenRegion(0, 0, 16, 16).is_valid is True
