from django.urls import path

from .views import (
    IFoodDisconnectView,
    IFoodOAuthStartView,
    IntegrationStatusView,
    ifood_oauth_callback,
    ninetynine_connect,
    ninetynine_disconnect,
)

urlpatterns = [
    # iFood OAuth (PR 12)
    path("connect/ifood/start/", IFoodOAuthStartView.as_view(), name="ifood-oauth-start"),
    path("connect/ifood/callback/", ifood_oauth_callback, name="ifood-oauth-callback"),
    path("connect/ifood/disconnect/", IFoodDisconnectView.as_view(), name="ifood-oauth-disconnect"),
    # 99Food Manual (PR 13)
    path("connect/99food/connect/", ninetynine_connect, name="99food-connect"),
    path("connect/99food/disconnect/", ninetynine_disconnect, name="99food-disconnect"),
    # Status
    path("connect/status/", IntegrationStatusView.as_view(), name="integration-status"),
]
