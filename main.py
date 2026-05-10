import pygame
import pygame.gfxdraw
from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CORNER_RADIUS,
    ICON_SIZE, COL_SPACING, ROW_SPACING, MARGIN_X, GRID_START_Y,
    COLOR_BLACK, COLOR_WHITE, COLOR_OFF_WHITE,
    APP_GREEN, APP_BLUE, APP_DARK_GREY, APP_ORANGE
)
from utils import draw_gradient_background
from components import (
    draw_icon,
    draw_weather_widget,
    draw_status_bar,
    draw_dock
)
from apps.health import HealthApp
from apps.health_admin import HealthAdminApp
from apps.splash_screen import show_splash_screen

def draw_app_grid(screen):
    #Draw app icons grid layout

    # Row 1 - 4 icons
    y1 = GRID_START_Y
    draw_icon(screen, MARGIN_X, y1, APP_GREEN, "Messages", "message")
    draw_icon(screen, MARGIN_X + (ICON_SIZE + COL_SPACING), y1,
              COLOR_OFF_WHITE, "Calendar", "calendar")
    draw_icon(screen, MARGIN_X + (ICON_SIZE + COL_SPACING) * 2, y1,
              COLOR_OFF_WHITE, "Health", "health")
    draw_icon(screen, MARGIN_X + (ICON_SIZE + COL_SPACING) * 3, y1,
              (200, 200, 200), "Camera", "camera")

    # Row 2 - 4 icons
    y2 = y1 + ICON_SIZE + ROW_SPACING
    draw_icon(screen, MARGIN_X, y2, COLOR_OFF_WHITE, "Clock", "clock")
    draw_icon(screen, MARGIN_X + (ICON_SIZE + COL_SPACING), y2, APP_GREEN, "Maps", "maps")
    draw_icon(screen, MARGIN_X + (ICON_SIZE + COL_SPACING) * 2, y2,
              APP_DARK_GREY, "Wallet", "wallet")
    draw_icon(screen, MARGIN_X + (ICON_SIZE + COL_SPACING) * 3, y2,
              COLOR_OFF_WHITE, "Notes", "notes")

    # Row 3 - 4 icons
    y3 = y2 + ICON_SIZE + ROW_SPACING
    draw_icon(screen, MARGIN_X, y3, COLOR_OFF_WHITE, "Reminders", "reminders")
    draw_icon(screen, MARGIN_X + (ICON_SIZE + COL_SPACING), y3, APP_DARK_GREY, "Stocks", "stocks")
    draw_icon(screen, MARGIN_X + (ICON_SIZE + COL_SPACING) * 2, y3,
              (20, 20, 20), "TV", "tv")
    draw_icon(screen, MARGIN_X + (ICON_SIZE + COL_SPACING) * 3, y3,
              APP_BLUE, "App Store", "appstore")

    # Row 4 - Health Admin
    y4 = y3 + ICON_SIZE + ROW_SPACING
    draw_icon(screen, MARGIN_X, y4, APP_ORANGE, "Admin", "admin")

    # Weather Widget
    draw_weather_widget(screen, y4)

def draw_page_dots(screen):
    dot_y = SCREEN_HEIGHT - 145
    center_x = SCREEN_WIDTH // 2

    # Active dot (white)
    pygame.gfxdraw.aacircle(screen, center_x - 15, dot_y, 3, COLOR_WHITE)
    pygame.gfxdraw.filled_circle(screen, center_x - 15, dot_y, 3, COLOR_WHITE)

    # Inactive dots (grey)
    grey = (150, 150, 150)
    pygame.gfxdraw.aacircle(screen, center_x, dot_y, 3, grey)
    pygame.gfxdraw.filled_circle(screen, center_x, dot_y, 3, grey)

    pygame.gfxdraw.aacircle(screen, center_x + 15, dot_y, 3, grey)
    pygame.gfxdraw.filled_circle(screen, center_x + 15, dot_y, 3, grey)
2
def draw_bezel(screen):
    pygame.draw.rect(
        screen, COLOR_BLACK,
        (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT),
        10, border_radius=CORNER_RADIUS
    )

def draw_home_screen(screen):
    draw_gradient_background(screen)
    draw_status_bar(screen)
    draw_app_grid(screen)
    draw_page_dots(screen)
    draw_dock(screen)
    draw_bezel(screen)

def get_icon_rect(row, col):
    y = GRID_START_Y + row * (ICON_SIZE + ROW_SPACING)
    x = MARGIN_X + col * (ICON_SIZE + COL_SPACING)
    return pygame.Rect(x, y, ICON_SIZE, ICON_SIZE)

def check_icon_click(pos, row, col):
    return get_icon_rect(row, col).collidepoint(pos)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.NOFRAME)
    pygame.display.set_caption("iPhone Home Screen")
    clock = pygame.time.Clock()

    running = True
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    if check_icon_click(event.pos, 0, 2):
                        # Show splash screen
                        show_splash_screen(
                            screen,
                            (245, 245, 250),
                            "health"
                        )
                        # Open Health app
                        health_app = HealthApp(screen)
                        result = health_app.run()
                        if result == "quit":
                            running = False

                    elif check_icon_click(event.pos, 3, 0):
                        # Show splash screen
                        show_splash_screen(
                            screen,
                            (28, 28, 30),
                            "admin"
                        )
                        # Open Health Admin app
                        admin_app = HealthAdminApp(screen)
                        result = admin_app.run()
                        if result == "quit":
                            running = False

        # Drawing
        draw_home_screen(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()