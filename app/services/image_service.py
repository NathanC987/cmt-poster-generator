from PIL import Image, ImageDraw, ImageFont
import io
import os
import logging
import requests

logger = logging.getLogger(__name__)

class ImageService:
    """
    Service class for image processing operations using PIL.
    
    Provides methods for:
    - Opening images from URLs or local paths
    - Cropping images to specific aspect ratios
    - Saving processed images
    """
    def open_image(self, path_or_url):
        """
        Open an image from a URL or local file path.
        
        Args:
            path_or_url (str): URL or local path to the image
            
        Returns:
            PIL.Image: Opened image in RGBA format
        """
        logger.info(f"Opening image: {path_or_url}")
        if path_or_url.startswith("http"):
            resp = requests.get(path_or_url)
            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
        else:
            img = Image.open(path_or_url).convert("RGBA")
        logger.info(f"Image opened: {path_or_url} (size: {img.size})")
        return img

    def crop_to_aspect(self, img, target_size):
        """
        Crop an image to fill the target aspect ratio while maintaining quality.
        
        Args:
            img (PIL.Image): Source image to crop
            target_size (tuple): Target (width, height) dimensions
            
        Returns:
            PIL.Image: Cropped and resized image
        """
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
        """
        Save an image to the specified path.
        
        Args:
            img (PIL.Image): Image to save
            path (str): File path where the image will be saved
        """
        logger.info(f"Saving image to {path}")
        img.save(path, format="PNG")
