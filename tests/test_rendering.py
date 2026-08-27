"""Tests for the drawing helpers.

These render onto off-screen surfaces, so they need no display and check
pixels rather than appearance.
"""
import pygame
import pytest

import config
from utils import draw_gradient_background, draw_rounded_rect


@pytest.fixture
def surface():
    return pygame.Surface((config.SCREEN_WIDTH, 200), pygame.SRCALPHA)


class TestGradientBackground:

    def test_fills_every_row(self, surface):
        draw_gradient_background(surface)
        for y in (0, 99, 199):
            assert surface.get_at((0, y))[:3] != (0, 0, 0)

    def test_spans_the_full_width(self, surface):
        draw_gradient_background(surface)
        left = surface.get_at((0, 50))[:3]
        right = surface.get_at((config.SCREEN_WIDTH - 1, 50))[:3]
        assert left == right  # each row is one flat colour

    def test_the_top_band_is_the_flat_cyan(self, surface):
        draw_gradient_background(surface)
        assert surface.get_at((10, 10))[:3] == (0, 180, 210)

    def test_the_colour_changes_down_the_surface(self, surface):
        draw_gradient_background(surface)
        top = surface.get_at((10, 10))[:3]
        middle = surface.get_at((10, 120))[:3]
        bottom = surface.get_at((10, 195))[:3]
        assert top != middle != bottom

    def test_channel_values_stay_in_range(self, surface):
        draw_gradient_background(surface)
        for y in range(0, 200, 7):
            assert all(0 <= channel <= 255 for channel in surface.get_at((5, y))[:3])

    def test_a_one_pixel_tall_surface_does_not_divide_by_zero(self):
        draw_gradient_background(pygame.Surface((config.SCREEN_WIDTH, 1)))


class TestRoundedRect:

    def test_the_centre_is_filled(self, surface):
        draw_rounded_rect(surface, pygame.Rect(20, 20, 100, 100), (255, 0, 0, 255))
        assert surface.get_at((70, 70))[:3] == (255, 0, 0)

    def test_the_corners_are_cut_away(self, surface):
        draw_rounded_rect(surface, pygame.Rect(20, 20, 100, 100), (255, 0, 0, 255))
        assert surface.get_at((20, 20))[3] < 255  # top-left corner pixel

    def test_nothing_is_drawn_outside_the_rect(self, surface):
        draw_rounded_rect(surface, pygame.Rect(20, 20, 100, 100), (255, 0, 0, 255))
        assert surface.get_at((10, 10))[3] == 0

    def test_alpha_is_honoured(self, surface):
        draw_rounded_rect(surface, pygame.Rect(20, 20, 100, 100), (0, 0, 255, 128))
        assert surface.get_at((70, 70))[3] == 128

    def test_accepts_a_tuple_instead_of_a_rect(self, surface):
        draw_rounded_rect(surface, (20, 20, 100, 100), (0, 255, 0, 255))
        assert surface.get_at((70, 70))[:3] == (0, 255, 0)

    @pytest.mark.parametrize("radius", [0.1, 0.4, 1.0])
    def test_works_across_corner_radii(self, surface, radius):
        draw_rounded_rect(surface, pygame.Rect(20, 20, 100, 100), (255, 255, 0, 255), radius)
        assert surface.get_at((70, 70))[:3] == (255, 255, 0)

    def test_a_larger_radius_removes_more_of_the_corner(self, surface):
        sharp = pygame.Surface((200, 200), pygame.SRCALPHA)
        round_ = pygame.Surface((200, 200), pygame.SRCALPHA)
        draw_rounded_rect(sharp, pygame.Rect(20, 20, 100, 100), (255, 0, 0, 255), 0.1)
        draw_rounded_rect(round_, pygame.Rect(20, 20, 100, 100), (255, 0, 0, 255), 1.0)
        assert round_.get_at((25, 25))[3] < sharp.get_at((25, 25))[3]


class TestConfig:

    def test_the_screen_is_portrait(self):
        assert config.SCREEN_HEIGHT > config.SCREEN_WIDTH

    def test_the_icon_grid_is_horizontally_centred(self):
        # MARGIN_X is a hardcoded constant; this catches it drifting out of
        # step with the icon size or spacing
        row_width = 4 * config.ICON_SIZE + 3 * config.COL_SPACING
        assert config.MARGIN_X == (config.SCREEN_WIDTH - row_width) // 2

    def test_every_font_loaded(self):
        for name in ("FONT_TIME", "FONT_ICON", "FONT_WIDGET_BIG",
                     "FONT_WIDGET_MED", "FONT_WIDGET_SMALL"):
            assert getattr(config, name) is not None

    def test_fonts_can_render(self):
        assert config.FONT_TIME.render("09:41", True, (255, 255, 255)).get_width() > 0

    @pytest.mark.parametrize("name", [
        "COLOR_BLACK", "COLOR_WHITE", "COLOR_OFF_WHITE", "COLOR_GREY_TEXT",
        "APP_GREEN", "APP_BLUE", "APP_RED", "APP_ORANGE", "APP_GREY",
        "APP_DARK_GREY", "APP_WEATHER_BLUE",
    ])
    def test_colours_are_valid_rgb(self, name):
        colour = getattr(config, name)
        assert len(colour) == 3
        assert all(0 <= channel <= 255 for channel in colour)

    @pytest.mark.parametrize("name", ["COLOR_DOCK_BG", "COLOR_WIDGET_BG"])
    def test_translucent_colours_are_valid_rgba(self, name):
        colour = getattr(config, name)
        assert len(colour) == 4
        assert all(0 <= channel <= 255 for channel in colour)


class TestHomeScreenLayout:

    def test_icon_rects_are_positioned_on_the_grid(self):
        import main
        first = main.get_icon_rect(0, 0)
        assert first.topleft == (config.MARGIN_X, config.GRID_START_Y)
        assert first.size == (config.ICON_SIZE, config.ICON_SIZE)

    def test_columns_are_evenly_spaced(self):
        import main
        gap = main.get_icon_rect(0, 1).x - main.get_icon_rect(0, 0).x
        assert gap == config.ICON_SIZE + config.COL_SPACING

    def test_rows_are_evenly_spaced(self):
        import main
        gap = main.get_icon_rect(1, 0).y - main.get_icon_rect(0, 0).y
        assert gap == config.ICON_SIZE + config.ROW_SPACING

    def test_a_click_inside_an_icon_registers(self):
        import main
        assert main.check_icon_click(main.get_icon_rect(0, 2).center, 0, 2) is True

    def test_a_click_elsewhere_does_not(self):
        import main
        assert main.check_icon_click(main.get_icon_rect(0, 2).center, 1, 0) is False

    def test_the_last_column_fits_on_screen(self):
        import main
        assert main.get_icon_rect(0, 3).right <= config.SCREEN_WIDTH
