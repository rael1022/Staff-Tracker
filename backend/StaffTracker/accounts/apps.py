from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from django.contrib.auth.models import Group

        def create_default_groups(sender, **kwargs):
            for name in ['Employee', 'Trainer', 'HOD', 'HR']:
                Group.objects.get_or_create(name=name)

        post_migrate.connect(create_default_groups, sender=self)