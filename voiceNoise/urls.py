# voiceNoise/urls.py

from django.contrib import admin
from django.urls import path
from noiseapp.views import (
    index,                      # 홈페이지 UI
    separate_clicks,            # API 엔드포인트
)
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', index, name='index'),  # 홈페이지
    path('admin/', admin.site.urls),
    path('separate_clicks/', separate_clicks, name='separate_clicks'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
