from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import logging

logger = logging.getLogger('allauth')


# ✅ SETUP ALLAUTH LOGGING
def setup_allauth_logging():
    """Setup allauth OAuth2 debugging"""
    from allauth.socialaccount.providers.oauth2 import views as oauth2_views

    original_dispatch = oauth2_views.OAuth2Adapter.complete_login

    def debug_complete_login(self, request, app, **kwargs):
        logger.debug(f"🔵 ALLAUTH complete_login START")
        logger.debug(f"🔵 App: {app}")
        try:
            result = original_dispatch(self, request, app, **kwargs)
            logger.debug(f"🟢 ALLAUTH complete_login SUCCESS")
            return result
        except Exception as e:
            logger.error(f"🔴 ALLAUTH ERROR: {str(e)}", exc_info=True)
            raise

    oauth2_views.OAuth2Adapter.complete_login = debug_complete_login


# Pozovi na startup
setup_allauth_logging()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', include('core.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

path('messages/', views.my_messages, name='my_messages'),

