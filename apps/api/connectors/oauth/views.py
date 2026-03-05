"""OAuth views for iFood (and future providers) integration."""

import structlog
from django.conf import settings
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from connectors.ifood.oauth import IFoodOAuthClient, IFoodOAuthError

from .models import OAuthState

log = structlog.get_logger()


class IFoodOAuthStartView(APIView):
    """Start iFood OAuth flow.

    Returns JSON with authorization_url. Frontend handles redirect.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        store = getattr(request, "scope_store", None)
        if not store:
            return Response({"error": "X-Store-Id header required"}, status=400)

        oauth_state = OAuthState.objects.create(
            store=store,
            user=request.user,
            provider="ifood",
        )

        client = IFoodOAuthClient()
        authorization_url = client.get_authorization_url(oauth_state.state)

        log.info(
            "ifood_oauth_flow_started",
            store_id=str(store.id),
            user_id=str(request.user.id),
            state=oauth_state.state[:8],
        )

        return Response({"authorization_url": authorization_url})


@csrf_exempt
def ifood_oauth_callback(request):
    """Handle iFood OAuth callback.

    Public endpoint (no auth) — security via OAuthState anti-CSRF token.
    Redirects to frontend success or error page.
    """
    code = request.GET.get("code")
    state = request.GET.get("state")
    error = request.GET.get("error")

    frontend_base = settings.FRONTEND_BASE_URL

    if error:
        log.warning("ifood_oauth_callback_error_from_provider", error=error)
        return HttpResponseRedirect(f"{frontend_base}/integrations?oauth=error&reason=provider_denied")

    if not code or not state:
        log.warning("ifood_oauth_callback_missing_params", has_code=bool(code), has_state=bool(state))
        return HttpResponseRedirect(f"{frontend_base}/integrations?oauth=error&reason=missing_params")

    # Validate state
    try:
        oauth_state = OAuthState.objects.select_related("store").get(state=state, provider="ifood")
    except OAuthState.DoesNotExist:
        log.warning("ifood_oauth_callback_invalid_state", state=state[:8] if state else "")
        return HttpResponseRedirect(f"{frontend_base}/integrations?oauth=error&reason=invalid_state")

    if not oauth_state.is_valid:
        reason = "expired" if oauth_state.is_expired else "already_used"
        log.warning("ifood_oauth_callback_state_invalid", state=state[:8], reason=reason)
        return HttpResponseRedirect(f"{frontend_base}/integrations?oauth=error&reason={reason}")

    # Mark state as used
    oauth_state.used = True
    oauth_state.save(update_fields=["used"])

    store = oauth_state.store

    # Exchange code for tokens
    client = IFoodOAuthClient()
    try:
        token_data = client.exchange_code_for_token(code)
    except IFoodOAuthError as exc:
        log.error("ifood_oauth_callback_token_exchange_failed", store_id=str(store.id), error=str(exc))
        return HttpResponseRedirect(f"{frontend_base}/integrations?oauth=error&reason=token_exchange_failed")

    # Discover merchant IDs
    access_token = token_data.get("access_token", "")
    try:
        merchant_ids = client.get_merchant_ids(access_token)
    except IFoodOAuthError as exc:
        log.error("ifood_oauth_callback_merchant_discovery_failed", store_id=str(store.id), error=str(exc))
        return HttpResponseRedirect(f"{frontend_base}/integrations?oauth=error&reason=merchant_discovery_failed")

    if not merchant_ids:
        log.warning("ifood_oauth_callback_no_merchants", store_id=str(store.id))
        return HttpResponseRedirect(f"{frontend_base}/integrations?oauth=error&reason=no_merchants")

    # Save credentials (use first merchant)
    merchant_id = merchant_ids[0]
    client.save_credentials(store, token_data, merchant_id)

    log.info(
        "ifood_oauth_flow_completed",
        store_id=str(store.id),
        merchant_id=merchant_id,
    )

    return HttpResponseRedirect(f"{frontend_base}/integrations?oauth=success&provider=ifood")


class IFoodDisconnectView(APIView):
    """Disconnect iFood integration by deactivating credentials."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        store = getattr(request, "scope_store", None)
        if not store:
            return Response({"error": "X-Store-Id header required"}, status=400)

        from connectors.ifood.models import IFoodStoreCredential

        updated = IFoodStoreCredential.objects.filter(store=store, is_active=True).update(is_active=False)

        if updated == 0:
            return Response({"detail": "No active iFood connection found"}, status=404)

        log.info("ifood_oauth_disconnected", store_id=str(store.id))
        return Response({"detail": "iFood disconnected successfully"})


class IntegrationStatusView(APIView):
    """Return connection status for all integrations (iFood, 99Food)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        store_id = request.query_params.get("store_id", "")
        store = getattr(request, "scope_store", None)

        from connectors.ifood.models import IFoodStoreCredential
        from connectors.ninetynine.models import NinetyNineStoreCredential

        lookup_id = store_id or (str(store.id) if store else "")
        if not lookup_id:
            return Response({"error": "store_id or X-Store-Id header required"}, status=400)

        # iFood status
        ifood_status = {"status": "disconnected"}
        try:
            ifood_cred = IFoodStoreCredential.objects.get(store_id=lookup_id, is_active=True)
            ifood_status = {
                "status": "connected",
                "merchant_id": ifood_cred.merchant_id,
            }
        except IFoodStoreCredential.DoesNotExist:
            pass

        # 99Food status
        ninetynine_status = {"status": "disconnected"}
        try:
            nn_cred = NinetyNineStoreCredential.objects.get(store_id=lookup_id, is_active=True)
            ninetynine_status = {
                "status": "connected",
                "merchant_id": nn_cred.merchant_id,
            }
        except NinetyNineStoreCredential.DoesNotExist:
            pass

        return Response({
            "store_id": lookup_id,
            "ifood": ifood_status,
            "ninetynine": ninetynine_status,
        })


# ============================================================
# 99FOOD — Manual Connection via AppShopID (PR 13)
# ============================================================


@csrf_exempt
def ninetynine_connect(request):
    """Connect 99Food via AppShopID.

    POST /api/v1/connect/99food/connect/
    Body: {
        "store_id": "<uuid>",
        "app_shop_id": "<AppShopID from 99Food panel>",
        "store_name": "<optional name>"
    }
    """
    import json

    from django.http import JsonResponse

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Metodo nao permitido"}, status=405)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "JSON invalido"}, status=400)

    store_id = data.get("store_id", "").strip()
    app_shop_id = data.get("app_shop_id", "").strip()

    if not store_id:
        return JsonResponse({"error": "store_id e obrigatorio"}, status=400)

    if not app_shop_id:
        return JsonResponse(
            {"error": "AppShopID e obrigatorio. Encontre-o no painel do 99Food."},
            status=400,
        )

    from tenants.models import Membership, Store

    user_tenant_ids = Membership.objects.filter(
        user=request.user,
        is_active=True,
    ).values_list("tenant_id", flat=True)

    try:
        store = Store.objects.get(
            id=store_id,
            company__tenant_id__in=user_tenant_ids,
        )
    except Store.DoesNotExist:
        return JsonResponse({"error": "Store nao encontrada"}, status=404)

    from connectors.ninetynine.oauth import NinetyNineAuthClient, NinetyNineAuthError

    try:
        client = NinetyNineAuthClient(app_shop_id=app_shop_id)
        result = client.validate_credentials()

        token_data = result["token_data"]
        stores = result["stores"]

        merchant_id = ""
        if stores and isinstance(stores[0], dict):
            merchant_id = stores[0].get("id", "") or stores[0].get("merchantId", app_shop_id)

        client.save_credentials(store, token_data, merchant_id or app_shop_id)

        from connectors.ninetynine.polling import start_polling_for_ninetynine_store

        start_polling_for_ninetynine_store.delay(str(store.id))

        log.info(
            "99food_connected",
            store_id=str(store.id),
            merchant_id=merchant_id,
        )

        return JsonResponse(
            {
                "connected": True,
                "provider": "99food",
                "merchant_id": merchant_id or app_shop_id,
                "store_name": data.get("store_name", ""),
            }
        )

    except NinetyNineAuthError as exc:
        log.warning(
            "99food_connect_failed",
            error=str(exc),
            store_id=store_id,
        )
        return JsonResponse({"error": str(exc)}, status=400)

    except Exception as exc:
        log.error(
            "99food_connect_unexpected_error",
            error=str(exc),
            store_id=store_id,
        )
        return JsonResponse(
            {"error": "Erro inesperado. Tente novamente ou contate o suporte."},
            status=500,
        )


@csrf_exempt
def ninetynine_disconnect(request):
    """Disconnect 99Food from a store.

    POST /api/v1/connect/99food/disconnect/
    Body: {"store_id": "<uuid>"}
    """
    import json

    from django.http import JsonResponse

    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    if request.method != "POST":
        return JsonResponse({"error": "Metodo nao permitido"}, status=405)

    try:
        data = json.loads(request.body)
        store_id = data.get("store_id", "").strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"error": "JSON invalido"}, status=400)

    from connectors.ninetynine.models import NinetyNineStoreCredential
    from tenants.models import Membership, Store

    user_tenant_ids = Membership.objects.filter(
        user=request.user,
        is_active=True,
    ).values_list("tenant_id", flat=True)

    try:
        store = Store.objects.get(
            id=store_id,
            company__tenant_id__in=user_tenant_ids,
        )
        cred = NinetyNineStoreCredential.objects.get(store=store)
        cred.is_active = False
        cred.access_token = ""
        cred.save(update_fields=["is_active", "access_token"])

        log.info("99food_disconnected", store_id=str(store.id))
        return JsonResponse({"disconnected": True})

    except (Store.DoesNotExist, NinetyNineStoreCredential.DoesNotExist):
        return JsonResponse(
            {"error": "Store ou credencial nao encontrada"},
            status=404,
        )
