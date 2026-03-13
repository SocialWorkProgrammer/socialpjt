from django.urls import path

from . import views

app_name = "services"

urlpatterns = [
    path("", views.service_list, name="service_list"),
    path("api/", views.service_list_api, name="service_list_api"),
    path("api/<int:service_id>/", views.service_detail_api, name="service_detail_api"),
    path("recommend/", views.recommend_services, name="recommend_services"),
    path("chat/", views.chat_recommendation, name="chat_recommendation"),
    path("<int:service_id>/", views.service_detail, name="service_detail"),
]
