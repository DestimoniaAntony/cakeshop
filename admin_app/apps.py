from django.apps import AppConfig


class AdminAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'admin_app'
    
    def ready(self):
        """Import signals when app is ready"""
        import admin_app.signals