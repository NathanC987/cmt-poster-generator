from PIL import Image, ImageDraw, ImageFont
import io
import os
import logging

logger = logging.getLogger(__name__)

class ImageService:
    def open_image(self, path_or_url):
        logger.info(f"Opening image: {path_or_url}")
        if path_or_url.startswith("http"):
            import requests
            resp = requests.get(path_or_url)
            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        else:
            img = Image.open(path_or_url).convert("RGBA")
        logger.info(f"Image opened: {path_or_url} (size: {img.size})")
        return img

    def resize_and_center(self, img, size):
        logger.info(f"Resizing and centering image to {size}")
        img.thumbnail(size, Image.Resampling.LANCZOS)
        bg = Image.new("RGBA", size, (0,0,0,0))
        bg.paste(img, ((size[0]-img.width)//2, (size[1]-img.height)//2), img)
        return bg

    def save_image(self, img, path):
        logger.info(f"Saving image to {path}")
        img.save(path, format="PNG")
