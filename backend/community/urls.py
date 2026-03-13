from django.urls import path

from . import views

app_name = "community"

urlpatterns = [
    path("", views.community_list, name="community_list"),
    path("api/", views.community_list_api, name="community_list_api"),
    path("api/<int:post_id>/", views.community_detail_api, name="community_detail_api"),
]
