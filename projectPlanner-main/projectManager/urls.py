from django.contrib import admin
from django.urls import include, path
from sesame.views import LoginView
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("sesame/login/", LoginView.as_view(), name="sesame-login"),
    path('admin/', admin.site.urls, name='admin'),
    path("login/", views.EmailLoginView.as_view(),name="email_login"),
    path("login/auth/", LoginView.as_view(), name="login"),
    path('stripe/', include('subscriptions.urls')),
    ]
