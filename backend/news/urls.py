from django.urls import path

from . import views

app_name = "news"

urlpatterns = [
    path("", views.news_list, name="news_list"),
    path("<int:news_id>/", views.news_detail, name="news_detail"),
    path(
        "<int:news_id>/comments/<int:comment_id>/delete/",
        views.comment_delete,
        name="comment_delete",
    ),
]
