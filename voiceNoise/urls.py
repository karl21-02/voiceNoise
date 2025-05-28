# voiceNoise/urls.py

from django.contrib import admin
from django.urls import path
from noiseapp.views import (
    separate_clicks,            # ← import your new view
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('separate_clicks/', separate_clicks, name='separate_clicks'),  # ← add this
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
