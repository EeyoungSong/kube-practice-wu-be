from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from lingua_management.views.review_views import GraphDataView

def health_check(request):
    return JsonResponse({'status': 'healthy'})

schema_view = get_schema_view(
   openapi.Info(
      title="OCR Wordbook API",
      default_version='v1',
      description="API documentation for the OCR Wordbook application.",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@example.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('api/v1/', include('lingua_core.urls', namespace='lingua_core')),
    path('api/v1/', include('lingua_management.urls', namespace='lingua_management')),
    path('api/v1/accounts/', include('accounts.urls', namespace='accounts')),
    
    # User authentication URLs
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # Swagger API docs
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# 로컬 개발 환경에서 정적 파일 서빙
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
