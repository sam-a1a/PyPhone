from apps.health import HealthApp
from apps.health_admin import HealthAdminApp

class AppManager:

    APP_REGISTRY = {
        'health': HealthApp,
        'healthadmin': HealthAdminApp,
    }

    def __init__(self, screen):
        self.screen = screen
        self.current_app = None

    def launch_app(self, app_name):
        app_name = app_name.lower().replace(" ", "")

        if app_name in self.APP_REGISTRY:
            app_class = self.APP_REGISTRY[app_name]
            self.current_app = app_class(self.screen)
            result = self.current_app.run()
            self.current_app = None
            return result
        else:
            print(f"App not found: {app_name}")
            return "home"

    def is_app_available(self, app_name):
        app_name = app_name.lower().replace(" ", "")
        return app_name in self.APP_REGISTRY