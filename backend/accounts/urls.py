from django.urls import path
from django.contrib.auth import views as auth_views # django.contrib에서 제공하는 기본 뷰
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
    path("login/", auth_views.LoginView.as_view(template_name='accounts/login.html'), name="login"),
    # path("<int:pk>/", views.DetailView.as_view(), name="logout"),
    # path("<int:pk>/results/", views.ResultsView.as_view(), name="signin"),
    # path("<int:question_id>/vote/", views.vote, name="signout"),
    # path("", views, name="authenticate"), # 기관 인증
]
