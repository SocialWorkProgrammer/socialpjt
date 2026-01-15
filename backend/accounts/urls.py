from django.urls import path
from . import views

# 기본
# app_name = "polls"
# urlpatterns = [
#   path("", views.index, name = "index"),
#   path("<int:question_id>/", views.detail, name = "detail"),
#   path("<int:question_id>/results/", views.results, name = "results"),
#   path("<int:question_id>/vote/", views.vote, name = "vote"),
# ]

# 제너릭 뷰
# question_id 값이 pk로 바뀌었는데, 이는 제너릭 뷰에서는 pk를 사용하기 때문이다. 
app_name = "accounts"
urlpatterns = [
    path("", views.IndexView.as_view(), name="login"),
    path("<int:pk>/", views.DetailView.as_view(), name="logout"),
    path("<int:pk>/results/", views.ResultsView.as_view(), name="signin"),
    path("<int:question_id>/vote/", views.vote, name="signout"),
    path("", views, name="authenticate"), # 기관 인증
]
