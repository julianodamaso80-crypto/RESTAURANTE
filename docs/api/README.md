# API Collection — ERP Restaurante

## Como usar com Bruno

1. Instalar Bruno: https://www.usebruno.com/
2. Abrir Bruno → "Open Collection" → selecionar pasta `docs/api/bruno/`
3. Selecionar environment: `local` ou `staging`
4. Rodar `auth/login` primeiro para obter o token
5. O token é salvo automaticamente na variável `access_token`

## Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `base_url` | URL base da API |
| `access_token` | JWT token (preenchido pelo login) |
| `tenant_id` | UUID do tenant (pegar do response do login) |
| `company_id` | UUID da company |
| `store_id` | UUID da store |
| `catalog_id` | UUID do catálogo |
| `category_id` | UUID da categoria |
| `product_id` | UUID do produto |
| `customer_id` | UUID do cliente |
| `campaign_id` | UUID da campanha |
| `segment_id` | UUID do segmento |
| `stock_item_id` | UUID do item de estoque |
| `template_id` | UUID do template enterprise |

## Endpoints por domínio

| Domínio | Prefixo | Arquivos |
|---|---|---|
| Auth | `/api/v1/auth/` | login, refresh |
| Health | `/health/`, `/api/v1/health/` | health_check, worker_health, ifood_health |
| Orders | `/api/v1/orders/` | list, create, get, advance_status |
| Catalog | `/api/v1/catalogs/` | list, create, category, product, public, available |
| KDS | `/api/v1/kds/` | stations, tickets, update_status, metrics |
| CDP | `/api/v1/customers/` | list, create, consent, events, rfv, consents |
| CRM | `/api/v1/crm/` | segments, templates, campaigns, launch, runs, billing |
| Stock | `/api/v1/stock/` | items, movements, alerts, resolve, bom, recalculate |
| Enterprise | `/api/v1/enterprise/` | templates, onboard, reports, alerts |

## Endpoints públicos (sem auth)

- `GET /health/` — Health check
- `GET /api/v1/health/worker/` — Status do Celery worker
- `GET /api/v1/health/ifood/` — Status do conector iFood
- `POST /api/v1/auth/login/` — Obter JWT token
- `POST /api/v1/auth/refresh/` — Renovar JWT token
- `GET /api/v1/catalogs/{id}/public/` — Catálogo público
- `POST /api/v1/webhooks/ifood/` — Webhook iFood (validação por assinatura)

## Headers obrigatórios (endpoints autenticados)

```
Authorization: Bearer {{access_token}}
X-Tenant-ID: {{tenant_id}}
X-Store-ID: {{store_id}}
```

## Credenciais de demo (após rodar seed)

- Email: `owner@burguerpala.ce`
- Senha: `demo123`

## Status de pedido (FSM)

```
PENDING → CONFIRMED → PREPARING → READY → DELIVERY_PENDING → DELIVERED
                                                              ↘ CANCELLED
```

Qualquer estado pode transicionar para `CANCELLED`.
