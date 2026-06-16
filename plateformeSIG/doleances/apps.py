from django.apps import AppConfig


class DoleancesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'doleances'
    verbose_name = 'Doléances & Demandes'

    def ready(self):
        import doleances.signals  # noqa: F401 — enregistre les signaux post_save
