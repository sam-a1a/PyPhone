"""Tests for the notification banner.

Rendering happens on an off-screen surface and the animation is driven with an
explicit dt, so nothing here depends on real time or a display.
"""
import pygame
import pytest

from components.notification import (
    BANNER_HEIGHT, BANNER_RESTING_Y, SLIDE_IN_SECONDS, SLIDE_OUT_SECONDS,
    NotificationBanner,
)
from config import SCREEN_WIDTH


@pytest.fixture
def banner():
    return NotificationBanner()


@pytest.fixture
def surface():
    return pygame.Surface((SCREEN_WIDTH, 850), pygame.SRCALPHA)


def shown(banner, **kwargs):
    banner.show("Health", "Verification code", "123456 is your code.",
                icon_name="health", **kwargs)
    return banner


class TestInitialState:

    def test_starts_hidden(self, banner):
        assert banner.visible is False

    def test_sits_off_screen_when_hidden(self, banner):
        assert banner.current_y() < 0

    def test_drawing_while_hidden_paints_nothing(self, banner, surface):
        banner.draw(surface)
        assert surface.get_at((SCREEN_WIDTH // 2, BANNER_RESTING_Y + 10))[3] == 0

    def test_updating_while_hidden_is_harmless(self, banner):
        banner.update(0.5)
        assert banner.visible is False


class TestShowing:

    def test_showing_makes_it_visible(self, banner):
        shown(banner)
        assert banner.visible is True

    def test_the_app_name_is_upper_cased(self, banner):
        shown(banner)
        assert banner.app_name == "HEALTH"

    def test_the_title_and_body_are_kept(self, banner):
        shown(banner)
        assert banner.title == "Verification code"
        assert "123456" in banner.body

    def test_it_starts_off_screen(self, banner):
        shown(banner)
        assert banner.current_y() < 0

    def test_a_missing_icon_falls_back_rather_than_failing(self, banner):
        banner.show("Health", "T", "B", icon_name="definitely-not-an-icon")
        assert banner.icon is not None

    def test_it_works_with_no_icon_at_all(self, banner, surface):
        banner.show("Health", "T", "B")
        assert banner.icon is None
        banner.draw(surface)

    def test_showing_again_replaces_the_current_banner(self, banner):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        banner.show("Admin", "Second", "Replaced")
        assert banner.title == "Second"
        assert banner.current_y() < 0  # animates in from the top again


class TestSlideAnimation:

    def test_it_slides_downwards(self, banner):
        shown(banner)
        first = banner.current_y()
        banner.update(SLIDE_IN_SECONDS / 3)
        second = banner.current_y()
        banner.update(SLIDE_IN_SECONDS / 3)
        assert first < second < banner.current_y()

    def test_it_comes_to_rest_in_position(self, banner):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        assert banner.current_y() == BANNER_RESTING_Y

    def test_it_holds_in_place(self, banner):
        shown(banner, hold_seconds=2.0)
        banner.update(SLIDE_IN_SECONDS)
        banner.update(1.0)
        assert banner.current_y() == BANNER_RESTING_Y
        assert banner.visible is True

    def test_it_leaves_after_the_hold(self, banner):
        shown(banner, hold_seconds=1.0)
        banner.update(SLIDE_IN_SECONDS)
        banner.update(1.0)
        banner.update(SLIDE_OUT_SECONDS / 2)
        assert banner.current_y() < BANNER_RESTING_Y

    def test_it_is_gone_once_the_exit_finishes(self, banner):
        shown(banner, hold_seconds=0.5)
        banner.update(SLIDE_IN_SECONDS)
        banner.update(0.5)
        banner.update(SLIDE_OUT_SECONDS)
        assert banner.visible is False

    def test_the_slide_eases_rather_than_running_linearly(self, banner):
        # Ease-out: most of the distance is covered in the first half
        shown(banner)
        banner.update(SLIDE_IN_SECONDS / 2)
        halfway = banner.current_y()
        start = -(BANNER_HEIGHT + 20)
        travelled = (halfway - start) / (BANNER_RESTING_Y - start)
        assert travelled > 0.5


class TestDismissing:

    def test_dismiss_starts_the_exit(self, banner):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        banner.dismiss()
        banner.update(SLIDE_OUT_SECONDS)
        assert banner.visible is False

    def test_dismissing_while_hidden_is_harmless(self, banner):
        banner.dismiss()
        assert banner.visible is False

    def test_hide_removes_it_at_once(self, banner):
        shown(banner)
        banner.hide()
        assert banner.visible is False
        assert banner.current_y() < 0


class TestTapping:

    def tap(self, pos):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=pos, button=1)

    def test_a_tap_on_the_banner_is_swallowed(self, banner):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        assert banner.handle_event(self.tap(banner.get_rect().center)) is True

    def test_a_tap_on_the_banner_dismisses_it(self, banner):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        banner.handle_event(self.tap(banner.get_rect().center))
        banner.update(SLIDE_OUT_SECONDS)
        assert banner.visible is False

    def test_a_tap_elsewhere_passes_through(self, banner):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        assert banner.handle_event(self.tap((SCREEN_WIDTH // 2, 700))) is False

    def test_taps_pass_through_while_hidden(self, banner):
        assert banner.handle_event(self.tap((100, 60))) is False

    def test_taps_pass_through_once_it_is_leaving(self, banner):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        banner.dismiss()
        assert banner.handle_event(self.tap(banner.get_rect().center)) is False

    def test_a_non_click_event_is_ignored(self, banner):
        shown(banner)
        event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a, unicode="a")
        assert banner.handle_event(event) is False


class TestDrawing:

    def test_it_paints_within_the_screen(self, banner, surface):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        rect = banner.get_rect()
        assert rect.left >= 0
        assert rect.right <= SCREEN_WIDTH

    def test_it_paints_something(self, banner, surface):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        banner.draw(surface)
        assert surface.get_at(banner.get_rect().center)[3] > 0

    def test_it_sits_below_the_status_bar(self, banner):
        shown(banner)
        banner.update(SLIDE_IN_SECONDS)
        assert banner.get_rect().top >= 44

    def test_a_long_body_is_truncated_to_fit(self, banner, surface):
        banner.show("Health", "Title", "x" * 400)
        banner.update(SLIDE_IN_SECONDS)
        banner.draw(surface)   # must not overflow or raise

    def test_truncation_leaves_short_text_alone(self, banner):
        from components.notification import FONT_BODY
        assert banner._truncate("short", FONT_BODY, 500) == "short"

    def test_truncation_adds_an_ellipsis(self, banner):
        from components.notification import FONT_BODY
        assert banner._truncate("x" * 200, FONT_BODY, 100).endswith("...")

    def test_update_without_a_dt_uses_the_clock(self, banner):
        # The app calls update() with no argument once a frame
        shown(banner)
        banner.update()
        assert banner.visible is True
