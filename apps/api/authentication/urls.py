from django.urls import path

from authentication.views import login_view, refresh_view, register_view

urlpatterns = [
    path("login/", login_view, name="token_obtain_pair"),
    path("refresh/", refresh_view, name="token_refresh"),
    path("register/", register_view, name="register"),
]
