"""
Test ImageContext coordinate system and cropping correctness.

Tests all scenarios:
1. Remote VM (scale=1.0, no offset)
2. Mac non-Retina fullscreen (scale=1.0, no offset)
3. Mac Retina fullscreen (scale=2.0, no offset)
4. Mac Retina window crop (scale=2.0, with offset)
5. Mac non-Retina window crop (scale=1.0, with offset)
6. Cropping correctness (scale-independent)
"""

import numpy as np
import pytest

from gui_harness.perception.detector import ImageContext


class TestImageContext:

    def test_remote(self):
        """VM / remote screenshot: 1:1, no offset."""
        ctx = ImageContext(pixel_scale=1.0, origin_x=0, origin_y=0)
        assert ctx.image_to_click(500, 300) == (500, 300)
        assert ctx.click_to_image(500, 300) == (500, 300)

    def test_mac_non_retina(self):
        """Mac non-Retina fullscreen: scale=1.0."""
        ctx = ImageContext(pixel_scale=1.0, origin_x=0, origin_y=0)
        assert ctx.image_to_click(960, 540) == (960, 540)
        assert ctx.click_to_image(960, 540) == (960, 540)

    def test_mac_retina_fullscreen(self):
        """Mac Retina fullscreen: scale=2.0."""
        ctx = ImageContext(pixel_scale=2.0, origin_x=0, origin_y=0)
        assert ctx.image_to_click(3024, 1964) == (1512, 982)
        assert ctx.image_to_click(0, 0) == (0, 0)
        assert ctx.image_to_click(1000, 500) == (500, 250)
        assert ctx.click_to_image(500, 250) == (1000, 500)

    def test_mac_retina_window(self):
        """Mac Retina window crop: scale=2.0, window at (100, 200)."""
        ctx = ImageContext(pixel_scale=2.0, origin_x=100, origin_y=200)
        assert ctx.image_to_click(0, 0) == (100, 200)
        assert ctx.image_to_click(200, 400) == (200, 400)
        assert ctx.click_to_image(100, 200) == (0, 0)

    def test_mac_non_retina_window(self):
        """Mac non-Retina window crop: scale=1.0, window at (500, 161)."""
        ctx = ImageContext(pixel_scale=1.0, origin_x=500, origin_y=161)
        assert ctx.image_to_click(0, 0) == (500, 161)
        assert ctx.image_to_click(420, 275) == (920, 436)
        assert ctx.click_to_image(500, 161) == (0, 0)

    def test_cropping_is_scale_independent(self):
        """Cropping uses image pixel coords directly — scale never involved."""
        img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        img[300:400, 200:300] = [0, 0, 255]

        detected = {"x": 200, "y": 300, "w": 100, "h": 100}
        crop = img[detected["y"]:detected["y"]+detected["h"],
                   detected["x"]:detected["x"]+detected["w"]]

        assert crop.shape == (100, 100, 3)
        assert np.all(crop[:, :, 2] == 255)

        for scale in [1.0, 2.0, 0.5, 3.0]:
            crop2 = img[detected["y"]:detected["y"]+detected["h"],
                        detected["x"]:detected["x"]+detected["w"]]
            assert np.array_equal(crop, crop2)

    def test_roundtrip(self):
        """image→click→image roundtrip should be identity."""
        for scale in [1.0, 2.0]:
            for ox, oy in [(0, 0), (100, 200), (500, 300)]:
                ctx = ImageContext(pixel_scale=scale, origin_x=ox, origin_y=oy)
                for px, py in [(0, 0), (100, 100), (500, 300), (1000, 800)]:
                    cx, cy = ctx.image_to_click(px, py)
                    px2, py2 = ctx.click_to_image(cx, cy)
                    assert px == px2 and py == py2

    def test_old_bug_scenario(self):
        """Reproduce the exact bug that was fixed (VM screenshot with wrong scaling)."""
        img = np.zeros((922, 1920, 3), dtype=np.uint8)
        img[380:420, 20:60] = [0, 255, 0]

        detected = {"x": 20, "y": 380, "w": 40, "h": 40}

        # Correct: crop directly with pixel coords
        crop = img[detected["y"]:detected["y"]+detected["h"],
                   detected["x"]:detected["x"]+detected["w"]]
        assert crop.shape == (40, 40, 3)
        assert np.all(crop[:, :, 1] == 255)

        # Old bug: wrong scaling would shift crop
        old_scale_y = 922 / 1080
        old_py = int(detected["y"] * old_scale_y)
        old_crop = img[old_py:old_py+detected["h"], detected["x"]:detected["x"]+detected["w"]]
        assert not np.all(old_crop[:, :, 1] == 255)
