"""Icon drawing functions with image support."""
import pygame
import pygame.gfxdraw
import os
from config import (
    ICON_SIZE, COLOR_WHITE,
    FONT_ICON
)

# Get the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_DIR = os.path.join(PROJECT_ROOT, "assets", "icons")

# Cache for loaded icons
_icon_cache = {}
_fallback_cache = {}


def draw_smooth_circle(surface, color, center, radius):
    """Draw an anti-aliased smooth circle."""
    x, y = int(center[0]), int(center[1])
    r = int(radius)

    pygame.gfxdraw.aacircle(surface, x, y, r, color)
    pygame.gfxdraw.filled_circle(surface, x, y, r, color)


def draw_smooth_rounded_rect(surface, rect, color, radius=0.4):
    """Draw a smooth rounded rectangle (iOS style icon background)."""
    rect = pygame.Rect(rect)

    shape_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    corner_radius = int(min(rect.width, rect.height) * radius)

    pygame.draw.rect(shape_surf, color,
                     (corner_radius, 0, rect.width - 2 * corner_radius, rect.height))
    pygame.draw.rect(shape_surf, color,
                     (0, corner_radius, rect.width, rect.height - 2 * corner_radius))

    corners = [
        (corner_radius, corner_radius),
        (rect.width - corner_radius - 1, corner_radius),
        (corner_radius, rect.height - corner_radius - 1),
        (rect.width - corner_radius - 1, rect.height - corner_radius - 1),
    ]

    for cx, cy in corners:
        pygame.gfxdraw.aacircle(shape_surf, cx, cy, corner_radius, color)
        pygame.gfxdraw.filled_circle(shape_surf, cx, cy, corner_radius, color)

    surface.blit(shape_surf, rect.topleft)


def create_fallback_icon(color, size=None):
    """Create a beautiful fallback icon when PNG is missing."""
    if size is None:
        size = (ICON_SIZE, ICON_SIZE)

    cache_key = f"fallback_{color}_{size[0]}x{size[1]}"
    if cache_key in _fallback_cache:
        return _fallback_cache[cache_key]

    surface = pygame.Surface(size, pygame.SRCALPHA)
    draw_smooth_rounded_rect(surface, (0, 0, size[0], size[1]), color, radius=0.22)

    center = (size[0] // 2, size[1] // 2)
    inner_radius = size[0] // 4
    inner_color = (255, 255, 255, 200)
    draw_smooth_circle(surface, inner_color, center, inner_radius)

    highlight = pygame.Surface(size, pygame.SRCALPHA)
    for y in range(size[1] // 3):
        alpha = int(50 * (1 - y / (size[1] // 3)))
        pygame.draw.line(highlight, (255, 255, 255, alpha), (0, y), (size[0], y))

    mask_surf = pygame.Surface(size, pygame.SRCALPHA)
    draw_smooth_rounded_rect(mask_surf, (0, 0, size[0], size[1]), (255, 255, 255, 255), radius=0.22)
    highlight.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    surface.blit(highlight, (0, 0))

    _fallback_cache[cache_key] = surface
    return surface


def load_icon_image(icon_name, size=None):
    """Load an icon image by name.

    Args:
        icon_name: Name of the icon file (without extension)
        size: Tuple of (width, height) for scaling

    Returns:
        Scaled pygame Surface or None if loading fails
    """
    if size is None:
        size = (ICON_SIZE, ICON_SIZE)

    # Keep original name lowercase
    original_name = icon_name.lower()

    cache_key = f"{original_name}_{size[0]}x{size[1]}"

    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    # Try multiple filename variations in order of priority
    name_variations = [
        original_name,                              # health_admin (as-is)
        original_name.replace(" ", "_"),            # health_admin (spaces to underscore)
        original_name.replace(" ", ""),             # healthadmin (no spaces)
        original_name.replace("_", ""),             # healthadmin (no underscores)
        original_name.replace(" ", "").replace("_", ""),  # healthadmin (no spaces or underscores)
    ]

    # Remove duplicates while preserving order
    seen = set()
    unique_variations = []
    for name in name_variations:
        if name not in seen:
            seen.add(name)
            unique_variations.append(name)

    for name in unique_variations:
        png_path = os.path.join(ICON_DIR, f"{name}.png")

        if os.path.exists(png_path):
            try:
                image = pygame.image.load(png_path).convert_alpha()
                scaled = pygame.transform.smoothscale(image, size)
                _icon_cache[cache_key] = scaled
                return scaled
            except (pygame.error, FileNotFoundError, OSError) as e:
                print(f"Error loading {name}: {e}")
                continue

    return None


def draw_icon(screen, x, y, color, name, symbol_type=None):
    """Draws an app icon with its label.

    Args:
        screen: Pygame surface to draw on
        x: X coordinate of icon top-left
        y: Y coordinate of icon top-left
        color: Fallback background color if no image found
        name: Display name for the label
        symbol_type: Icon filename to load (uses name if not provided)
    """
    center_x = x + ICON_SIZE // 2
    center_y = y + ICON_SIZE // 2

    icon_name = symbol_type if symbol_type else name
    icon_image = load_icon_image(icon_name)

    if icon_image:
        img_rect = icon_image.get_rect(center=(center_x, center_y))
        screen.blit(icon_image, img_rect)
    else:
        fallback = create_fallback_icon(color)
        screen.blit(fallback, (x, y))

    if name:
        label = FONT_ICON.render(name, True, COLOR_WHITE)
        label_x = center_x - label.get_width() // 2
        label_y = y + ICON_SIZE + 5
        screen.blit(label, (label_x, label_y))


def draw_dock_icon(screen, x, y, color, symbol_type):
    """Draws a dock icon (no label)."""
    center_x = x + ICON_SIZE // 2
    center_y = y + ICON_SIZE // 2

    icon_image = load_icon_image(symbol_type)

    if icon_image:
        img_rect = icon_image.get_rect(center=(center_x, center_y))
        screen.blit(icon_image, img_rect)
    else:
        fallback = create_fallback_icon(color)
        screen.blit(fallback, (x, y))


def clear_icon_cache():
    """Clear all cached icons (useful for reloading)."""
    global _icon_cache, _fallback_cache
    _icon_cache.clear()
    _fallback_cache.clear()


def preload_icons(icon_names, size=None):
    """Preload multiple icons into cache."""
    for name in icon_names:
        load_icon_image(name, size)