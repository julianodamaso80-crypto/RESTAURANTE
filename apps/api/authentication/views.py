from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

login_view = TokenObtainPairView.as_view()
refresh_view = TokenRefreshView.as_view()
