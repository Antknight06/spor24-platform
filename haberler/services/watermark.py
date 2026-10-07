# haberler/services/watermark.py
import os
import logging
from PIL import Image, ImageFilter

from django.conf import settings

logger = logging.getLogger(__name__)

# Primary production path with local fallback
WATERMARK_PATH = '/var/www/ant_news_full/static/img/spor24_watermark.png'
if not os.path.exists(WATERMARK_PATH):
    local_candidate = os.path.join(settings.BASE_DIR, 'static', 'img', 'spor24_watermark.png')
    if os.path.exists(local_candidate):
        WATERMARK_PATH = local_candidate

def apply_spor24_watermark(image: Image.Image, position: str = 'top-right', size_ratio: float = 0.15, opacity: float = 0.50) -> Image.Image:
    """
    Applies the official SPOR24.net circular badge watermark onto a news image.
    Kenan Bey's standard: Top-right corner, 15% width of image, 50% opacity.
    
    :param image: PIL Image in RGB or RGBA mode.
    :param position: 'top-right' (default) or 'bottom-right'.
    :param size_ratio: Ratio of image width that watermark diameter should occupy (default 15%).
    :param opacity: Opacity multiplier (0.50 = 50% visible, 50% translucent).
    :return: Watermarked PIL Image in RGB format.
    """
    try:
        if not os.path.exists(WATERMARK_PATH):
            logger.warning(f"Watermark file not found at {WATERMARK_PATH}")
            return image

        # Ensure base image is RGBA
        base = image.convert('RGBA') if image.mode != 'RGBA' else image.copy()
        w, h = base.size

        # Load watermark logo
        wm = Image.open(WATERMARK_PATH).convert('RGBA')

        # Calculate watermark size (proportional to image width)
        target_w = max(80, min(220, int(w * size_ratio)))
        target_h = int(wm.height * (target_w / wm.width))
        wm_resized = wm.resize((target_w, target_h), Image.Resampling.LANCZOS)

        # Margin from border
        margin = max(18, int(w * 0.02))

        # Position calculation
        pos_x = w - target_w - margin
        if position == 'bottom-right':
            pos_y = h - target_h - margin
        else: # top-right
            pos_y = margin

        # Apply requested opacity (60% visible, 40% translucent)
        r, g, b, alpha = wm_resized.split()
        alpha_adjusted = alpha.point(lambda p: int(p * opacity))
        wm_transparent = Image.merge('RGBA', (r, g, b, alpha_adjusted))

        # Soft subtle drop shadow (proportional to opacity, ~30% max)
        shadow_padding = 14
        shadow_patch = Image.new('RGBA', (target_w + shadow_padding * 2, target_h + shadow_padding * 2), (0, 0, 0, 0))
        shadow_alpha = alpha.point(lambda p: int(p * (opacity * 0.5)))
        black_mask = Image.merge('RGBA', (
            Image.new('L', wm_resized.size, 0),
            Image.new('L', wm_resized.size, 0),
            Image.new('L', wm_resized.size, 0),
            shadow_alpha
        ))
        shadow_patch.paste(black_mask, (shadow_padding, shadow_padding), mask=shadow_alpha)
        shadow_patch = shadow_patch.filter(ImageFilter.GaussianBlur(radius=5))

        # Paste subtle shadow then translucent watermark
        base.paste(shadow_patch, (pos_x - shadow_padding, pos_y - shadow_padding), mask=shadow_patch)
        base.paste(wm_transparent, (pos_x, pos_y), mask=wm_transparent)

        return base.convert('RGB')
    except Exception as e:
        logger.error(f"Error applying spor24 watermark: {e}")
        return image

def watermark_news_file(file_path: str) -> bool:
    """
    Directly opens an existing news image file on disk, stamps the Spor24.net watermark
    (top-right, 15% width, 50% opacity), and overwrites it.
    """
    try:
        if not os.path.exists(file_path):
            return False
        with Image.open(file_path) as img:
            watermarked = apply_spor24_watermark(img)
            watermarked.save(file_path, format='JPEG', quality=88, optimize=True)
        return True
    except Exception as e:
        logger.error(f"Error watermarking news file {file_path}: {e}")
        return False

