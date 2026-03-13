from django.urls import path

from . import views

app_name = "services"

urlpatterns = [
    path("", views.service_list, name="service_list"),
    path("chat/", views.chat_recommendation, name="chat_recommendation"),
    path("<int:service_id>/", views.service_detail, name="service_detail"),
]
