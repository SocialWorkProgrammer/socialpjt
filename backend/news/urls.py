from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("", views.news_list, name="news_list"),
    path("api/", views.news_list_api, name="news_list_api"),
    path("api/<int:news_id>/", views.news_detail_api, name="news_detail_api"),
]
