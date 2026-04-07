from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from blog.views import signup, post_create, post_edit
from pages.views import page_not_found, server_error, permission_denied

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'
handler403 = 'pages.views.permission_denied'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/registration/', signup, name='registration'),
    path('auth/registration/', signup, name='auth_registration'),
    path('create/', post_create, name='create_post'),
    path('posts/<int:post_id>/edit/', post_edit, name='edit_post'),
    # Стандартные маршруты аутентификации
    path('accounts/', include('django.contrib.auth.urls')),
    # Переопределение маршрутов смены пароля
    path('auth/password_change/', auth_views.PasswordChangeView.as_view(), name='password_change'),
    path('auth/password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    # Основные маршруты блога и страниц
    path('', include(('blog.urls', 'blog'), namespace='blog')),
    path('pages/', include(('pages.urls', 'pages'), namespace='pages')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)