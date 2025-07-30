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

    def crop_to_aspect(self, img, target_size):
        logger.info(f"Cropping image to fill aspect ratio {target_size}")
        target_w, target_h = target_size
        src_w, src_h = img.size
        src_aspect = src_w / src_h
        target_aspect = target_w / target_h
        if src_aspect > target_aspect:
            # Source is wider than target: crop width
            new_w = int(target_aspect * src_h)
            left = (src_w - new_w) // 2
            img = img.crop((left, 0, left + new_w, src_h))
        else:
            # Source is taller than target: crop height
            new_h = int(src_w / target_aspect)
            top = (src_h - new_h) // 2
            img = img.crop((0, top, src_w, top + new_h))
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        return img

    def save_image(self, img, path):
        logger.info(f"Saving image to {path}")
        img.save(path, format="PNG")
