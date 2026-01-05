from django.apps import AppConfig
from django.db.models.signals import post_migrate

class DepartmentConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'department'

    def ready(self):
        from .models import Department

        def create_default_departments(sender, **kwargs):
            dept_names = ['IT', 'Finance', 'Marketing', 'Training', 'Ops', 'HR Ops']
            for name in dept_names:
                Department.objects.get_or_create(name=name)

        post_migrate.connect(create_default_departments, sender=self)
