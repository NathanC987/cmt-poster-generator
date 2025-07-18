import os
from PIL import ImageFont

FONT_PATH_BOLD = os.path.join(os.path.dirname(__file__), "../fonts/GlacialIndifference-Bold.ttf")
FONT_PATH_REGULAR = os.path.join(os.path.dirname(__file__), "../fonts/GlacialIndifference-Regular.ttf")

class FontService:
    """Font loader and manager for poster generation"""

    def get_title_font(self, size=110):
        return ImageFont.truetype(FONT_PATH_BOLD, size)

    def get_body_font(self, size=56):
        return ImageFont.truetype(FONT_PATH_REGULAR, size)

    def get_subtitle_font(self, size=60):
        return ImageFont.truetype(FONT_PATH_BOLD, size)

def get_font_service():
    return FontService()
