from django.urls import include, path
from . import views

urlpatterns = [
    path('', views.home, name='subscriptions-home'),
    path('home/', views.home, name='subscriptions-home'),
    path('config/', views.stripe_config),
    path('create-checkout-session/', views.create_checkout_session),
    path('success/', views.success, name='success'),
    path('cancel/', views.cancel, name='cancel'),
    path('webhook/', views.stripe_webhook),
    path('result/', views.result, name='result'),
]