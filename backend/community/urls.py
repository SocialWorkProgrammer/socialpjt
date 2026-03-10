from django.urls import path

from . import views

app_name = "community"

urlpatterns = [
    path("", views.community_list, name="community_list"),
    path("create/", views.community_create, name="community_create"),
    path("<int:post_id>/", views.community_detail, name="community_detail"),
    path("<int:post_id>/edit/", views.community_update, name="community_update"),
    path("<int:post_id>/delete/", views.community_delete, name="community_delete"),
    path(
        "<int:post_id>/comments/<int:comment_id>/delete/",
        views.comment_delete,
        name="comment_delete",
    ),
]
