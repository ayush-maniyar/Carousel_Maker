import os
import unittest
from unittest.mock import patch

from PIL import ImageFont

from renderer import load_font, render_carousel_slide


class RendererFontTests(unittest.TestCase):
    def test_load_font_returns_font_when_external_fonts_are_missing(self):
        with patch("renderer.ImageFont.truetype", side_effect=OSError("font unavailable")):
            font = load_font(24, "modern")
        self.assertIsNotNone(font)
        self.assertTrue(hasattr(font, "getbbox"))

    def test_render_slide_succeeds_with_builtin_font_fallback(self):
        os.makedirs("output_slides", exist_ok=True)
        filename = "renderer_font_fallback_test.png"
        path = os.path.join("output_slides", filename)
        try:
            with patch("renderer.ImageFont.truetype", side_effect=OSError("font unavailable")):
                result = render_carousel_slide(
                    {
                        "header": "Font fallback test",
                        "bullet_points": ["Rendering should work without system fonts."],
                        "slide_number": 1,
                        "total_slides": 1,
                    },
                    filename,
                )
            self.assertTrue(os.path.isfile(result))
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()
