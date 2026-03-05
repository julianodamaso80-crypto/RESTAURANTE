import structlog
from django.db import transaction
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from tenants.models import Company, Membership, Store, Tenant, User

log = structlog.get_logger()

login_view = TokenObtainPairView.as_view()
refresh_view = TokenRefreshView.as_view()


class RegisterSerializer(serializers.Serializer):
    nome_completo = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    senha = serializers.CharField(min_length=6, write_only=True)
    nome_restaurante = serializers.CharField(max_length=255)
    telefone = serializers.CharField(max_length=32, required=False, default="")


@api_view(["POST"])
@permission_classes([AllowAny])
def register_view(request):
    """Self-service registration.

    POST /api/v1/auth/register/
    Creates: User + Tenant + Company + Store + Membership
    Returns: JWT tokens + user info
    """
    ser = RegisterSerializer(data=request.data)
    ser.is_valid(raise_exception=True)
    data = ser.validated_data

    if User.objects.filter(email=data["email"]).exists():
        return Response(
            {"error": "Este email ja esta cadastrado."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    with transaction.atomic():
        user = User.objects.create_user(
            email=data["email"],
            password=data["senha"],
            name=data["nome_completo"],
        )

        slug = data["nome_restaurante"].lower().replace(" ", "-")[:50]
        tenant = Tenant.objects.create(name=data["nome_restaurante"], slug=slug)
        company = Company.objects.create(
            tenant=tenant,
            name=data["nome_restaurante"],
            slug="matriz",
        )
        store = Store.objects.create(
            company=company,
            name="Loja Principal",
            slug="principal",
        )
        Membership.objects.create(user=user, tenant=tenant)

    refresh = RefreshToken.for_user(user)

    log.info(
        "user_registered",
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        store_id=str(store.id),
    )

    return Response(
        {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.name,
                "role": "owner",
            },
            "tenant_id": str(tenant.id),
            "store_id": str(store.id),
        },
        status=status.HTTP_201_CREATED,
    )
