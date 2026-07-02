import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms.settings')

# Buat instance Celery dengan nama project
app = Celery('lms')

# Baca konfigurasi dari Django settings dengan prefix CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks dari semua app yang terdaftar di INSTALLED_APPS
app.autodiscover_tasks()
