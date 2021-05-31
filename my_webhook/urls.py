from django.urls import path

from . import views

urlpatterns = [
    path('', views.MyWebhookView.as_view()),
]
