import os
from typing import Dict, Optional
from PIL import ImageFont
from app.services.base_service import BaseService

class FontService(BaseService):
    """Font management service for poster generation"""
    
    def __init__(self, config: Dict = None):
        super().__init__(config)
        self.fonts = {}
        self.default_font = None
        
    async def _initialize(self):
        """Initialize font service with available fonts"""
        # Font paths to try (in order of preference)
        font_paths = [
            # Local app fonts
            "app/fonts/",
            # System fonts (Linux/Ubuntu - common on Render)
            "/usr/share/fonts/truetype/dejavu/",
            "/usr/share/fonts/truetype/liberation/",
            "/usr/share/fonts/TTF/",
            # System fonts (macOS)
            "/System/Library/Fonts/",
            "/Library/Fonts/",
            # System fonts (Windows)
            "C:/Windows/Fonts/",
        ]
        
        # Font files to look for (prioritizing Glacial Indifference)
        font_candidates = {
            "title": [
                "GlacialIndifference-Bold.ttf",
                "GlacialIndifference-Bold.otf",
                "glacial-indifference-bold.ttf",
                "DejaVuSans-Bold.ttf",
                "LiberationSans-Bold.ttf", 
                "Arial-Bold.ttf",
                "ArialBold.ttf"
            ],
            "subtitle": [
                "GlacialIndifference-Regular.ttf",
                "GlacialIndifference-Regular.otf",
                "glacial-indifference-regular.ttf",
                "GlacialIndifference.ttf",
                "glacial-indifference.ttf",
                "DejaVuSans.ttf",
                "LiberationSans-Regular.ttf",
                "Arial.ttf"
            ],
            "body": [
                "GlacialIndifference-Regular.ttf",
                "GlacialIndifference-Regular.otf",
                "glacial-indifference-regular.ttf",
                "GlacialIndifference.ttf",
                "glacial-indifference.ttf",
                "DejaVuSans.ttf",
                "LiberationSans-Regular.ttf",
                "Arial.ttf"
            ]
        }
        
        # Find available fonts
        for font_type, candidates in font_candidates.items():
            for path in font_paths:
                for font_file in candidates:
                    font_path = os.path.join(path, font_file)
                    if os.path.exists(font_path):
                        self.fonts[font_type] = font_path
                        print(f"Found {font_type} font: {font_path}")
                        break
                if font_type in self.fonts:
                    break
        
        # Set default font (PIL's default if nothing found)
        self.default_font = ImageFont.load_default()
        
        print(f"Font service initialized with {len(self.fonts)} system fonts")
    
    def get_font(self, font_type: str, size: int) -> ImageFont.ImageFont:
        """Get font by type and size"""
        try:
            if font_type in self.fonts:
                return ImageFont.truetype(self.fonts[font_type], size)
            else:
                # Fallback to default font
                return self.default_font
        except Exception as e:
            print(f"Error loading font {font_type}: {e}")
            return self.default_font
    
    def get_title_font(self, size: int = 48) -> ImageFont.ImageFont:
        """Get title font"""
        return self.get_font("title", size)
    
    def get_subtitle_font(self, size: int = 28) -> ImageFont.ImageFont:
        """Get subtitle font"""
        return self.get_font("subtitle", size)
    
    def get_body_font(self, size: int = 24) -> ImageFont.ImageFont:
        """Get body text font"""
        return self.get_font("body", size)
    
    def get_available_fonts(self) -> Dict[str, str]:
        """Get list of available fonts"""
        return self.fonts.copy()
    
    def test_fonts(self) -> Dict[str, any]:
        """Test font loading capabilities"""
        results = {
            "available_fonts": self.fonts,
            "default_font_available": self.default_font is not None,
            "test_results": {}
        }
        
        # Test each font type
        for font_type in ["title", "subtitle", "body"]:
            try:
                test_font = self.get_font(font_type, 24)
                results["test_results"][font_type] = {
                    "status": "success",
                    "font_path": self.fonts.get(font_type, "default")
                }
            except Exception as e:
                results["test_results"][font_type] = {
                    "status": "error", 
                    "error": str(e)
                }
        
        return results

# Global font service instance
_font_service = None

async def get_font_service() -> FontService:
    """Get global font service instance"""
    global _font_service
    if _font_service is None:
        _font_service = FontService()
        await _font_service.initialize()
    return _font_service
