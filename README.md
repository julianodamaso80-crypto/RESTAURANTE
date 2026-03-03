# Restaurante ERP SaaS

ERP e SaaS omnichannel para restaurantes, redes e franquias.

## Estrutura

```
├── apps/
│   ├── api/          # Backend Django + DRF
│   ├── worker/       # Celery workers (futuro)
│   └── web/          # Frontend (futuro)
├── packages/
│   └── shared/       # Código compartilhado (futuro)
├── docs/             # PRD, backlog e regras
├── docker-compose.yml
└── CLAUDE.md
```

## Pré-requisitos

- Python 3.12+
- Docker e Docker Compose
- pip

## Setup rápido

### 1. Subir dependências (Postgres e Redis)

```bash
docker compose up -d
```

### 2. Criar ambiente virtual e instalar dependências

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### 3. Rodar migrations

```bash
cd apps/api
python manage.py migrate
```

### 4. Criar superusuário

```bash
cd apps/api
python manage.py createsuperuser
```

### 5. Rodar o servidor de desenvolvimento

```bash
cd apps/api
python manage.py runserver
```

O endpoint de health estará em: http://localhost:8000/health/

### 6. Rodar testes

```bash
cd apps/api
pytest
```

### 7. Rodar lint

```bash
cd apps/api
ruff check .
```

## API — Guia rápido

### Autenticação

```bash
# Login (retorna access e refresh tokens)
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "sua-senha"}'

# Refresh token
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "<refresh-token>"}'
```

### Criar um Tenant

Requer superusuário.

```bash
curl -X POST http://localhost:8000/api/v1/tenants/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Group", "slug": "acme"}'
```

### Criar uma Company

Requer header `X-Tenant-Id` e permissão `companies:write`.

```bash
curl -X POST http://localhost:8000/api/v1/companies/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: <tenant-uuid>" \
  -d '{"tenant": "<tenant-uuid>", "name": "Acme Foods", "slug": "acme-foods"}'
```

### Criar uma Store

Requer header `X-Tenant-Id` (ou `X-Company-Id`) e permissão `stores:write`.

```bash
curl -X POST http://localhost:8000/api/v1/stores/ \
  -H "Authorization: Bearer <access-token>" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Id: <tenant-uuid>" \
  -d '{"company": "<company-uuid>", "name": "Loja Centro", "slug": "centro"}'
```

### Fluxo completo de setup

1. Faça login com o superusuário para obter o token JWT
2. Crie um Tenant (POST `/api/v1/tenants/`)
3. Crie Permissions via shell: `python manage.py shell` e `Permission.objects.create(codename="companies:write")`
4. Crie uma Company (POST `/api/v1/companies/`) com header `X-Tenant-Id`
5. Crie uma Store (POST `/api/v1/stores/`) com header `X-Tenant-Id`
6. Crie um User (POST `/api/v1/users/`) e um Membership (POST `/api/v1/memberships/`)
7. Crie um Role com Permissions e um RoleBinding para o User

### Endpoints disponíveis

| Método | Endpoint | Descrição | Acesso |
|--------|----------|-----------|--------|
| POST | `/api/v1/auth/login/` | Login JWT | Público |
| POST | `/api/v1/auth/refresh/` | Refresh token | Público |
| GET/POST | `/api/v1/tenants/` | Listar/criar tenants | Superuser |
| GET/POST | `/api/v1/companies/` | CRUD companies | RBAC |
| GET/POST | `/api/v1/stores/` | CRUD stores | RBAC |
| GET/POST | `/api/v1/users/` | CRUD users | RBAC |
| GET/POST | `/api/v1/memberships/` | CRUD memberships | RBAC |
| GET/POST | `/api/v1/roles/` | CRUD roles | RBAC |
| GET/POST | `/api/v1/role-bindings/` | CRUD role bindings | RBAC |
| GET | `/api/v1/permissions/` | Listar permissions | RBAC |
| GET | `/api/v1/audit/` | Listar audit events | RBAC |

### Headers de escopo

| Header | Descrição |
|--------|-----------|
| `X-Tenant-Id` | UUID do tenant |
| `X-Company-Id` | UUID da company (resolve tenant automaticamente) |
| `X-Store-Id` | UUID da store (resolve company e tenant automaticamente) |

## Domínio de Pedidos (PR 2)

### Rodar testes do PR 2

```bash
cd apps/api
pytest orders/tests/ -v
```

### Endpoints de pedidos

| Método | Endpoint | Descrição | Acesso |
|--------|----------|-----------|--------|
| POST | `/api/v1/orders/` | Criar pedido | Autenticado |
| GET | `/api/v1/orders/` | Listar pedidos da store | Autenticado |
| GET | `/api/v1/orders/{id}/` | Detalhar pedido | Autenticado |
| PATCH | `/api/v1/orders/{id}/status/` | Avançar estado (FSM) | Autenticado |

### Máquina de estados

```
PENDING → CONFIRMED → IN_PREPARATION → READY → DISPATCHED → DELIVERED
  ↓         ↓              ↓              ↓        ↓
CANCELLED  CANCELLED     CANCELLED     CANCELLED  CANCELLED
```

### O que NÃO está neste PR

- iFood connector
- Celery/worker
- Catálogo (OrderItem é snapshot intencional)
- KDS
- CRM / CDP
- Financeiro / conciliação

## Fila/Worker + Observabilidade (PR 3)

### Subir worker Celery

```bash
docker compose up worker
```

### Testar tarefa de forma síncrona

```bash
cd apps/api
python -c "
from core.tasks import example_async_task
result = example_async_task({'test': True})
print(result)
"
```

### Health check worker

```
GET /api/v1/health/worker/
→ 200 se workers ativos, 503 se nenhum worker
```

### Rodar testes do PR 3

```bash
cd apps/api
pytest core/tests/ -v
```

### Variáveis de ambiente novas

| Variável | Default | Descrição |
|---|---|---|
| `DJANGO_ENV` | `dev` | `prod` = logs JSON, `dev` = logs coloridos |

### O que NÃO está neste PR

- iFood connector (PR 4)
- Tarefas reais de negócio (só `example_async_task` de validação)
- Celery Beat / tarefas periódicas (roadmap)
- Monitoramento avançado de filas (Flower, Prometheus — roadmap)

## iFood Connector (PR 4)

### Webhook endpoint

```
POST /api/v1/webhooks/ifood/
Headers obrigatórios:
  X-IFood-Signature: <HMAC-SHA256 do payload>
Response: 202 Accepted (sempre < 2s)
```

### Pipeline de processamento

```
1. Validar assinatura X-IFood-Signature → 401 se inválida
2. Persistir RawEvent → imediato
3. Responder 202 → imediato
4. [Celery] Checar idempotência → skip se duplicado
5. [Celery] Buscar detalhes na API iFood (retry 404 com backoff)
6. [Celery] Criar Order interno
```

### Health check

```
GET /api/v1/health/ifood/
```

### Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `IFOOD_WEBHOOK_SECRET` | Secret para validar X-IFood-Signature |
| `IFOOD_API_BASE_URL` | Base URL da API iFood (default produção) |

### Rodar testes do PR 4

```bash
cd apps/api
pytest connectors/ifood/tests/ -v
```

### O que NÃO está neste PR (PR 4)

- OAuth / renovação de token iFood (próximo PR ou separado)
- Atualização de status de pedido via webhook iFood (só criação)

## iFood Polling (PR 12)

Alternativa ao webhook — polling ativo a cada 30 segundos via Celery Beat.
Funciona em qualquer ambiente sem precisar de endpoint público.

### Como funciona

```
1. Celery Beat dispara poll_ifood_orders a cada 30s
2. Para cada IFoodStoreCredential ativa com token:
   GET /order/v1.0/events:polling → eventos pendentes
3. Cria RawEvent + enfileira process_ifood_event (mesmo pipeline do webhook)
4. POST /order/v1.0/events/acknowledgment → remove da fila do iFood
```

### Coexistência com webhook

Webhook e polling podem rodar simultaneamente — idempotência por `event_id` previne duplicatas.
RawEvents de polling têm `headers.ingestion = "polling"` para distinguir.

### Subir Celery Beat

```bash
docker compose up beat
```

### Rodar testes do PR 12

```bash
cd apps/api
pytest connectors/ifood/tests/test_polling.py -v
```

## 99Food Connector (PR 11)

### Webhook endpoint

```
POST /api/v1/webhooks/99food/
Headers obrigatórios:
  X-Ninetynine-Signature: <HMAC-SHA256 do payload>
Response: 202 Accepted (sempre < 2s)
```

### Pipeline de processamento

```
1. Validar assinatura X-Ninetynine-Signature → 401 se inválida
2. Persistir RawEvent (source='99food') → imediato
3. Responder 202 → imediato
4. [Celery] Checar idempotência → skip se duplicado
5. [Celery] Buscar detalhes na API 99Food (retry 404 com backoff)
6. [Celery] Criar Order interno
```

### Health check

```
GET /api/v1/health/99food/
```

### Variáveis de ambiente

| Variável | Descrição |
|---|---|
| `NINETYNINE_WEBHOOK_SECRET` | Secret para validar X-Ninetynine-Signature |
| `NINETYNINE_API_BASE_URL` | Base URL da API 99Food |

### Rodar testes do PR 11

```bash
cd apps/api
pytest connectors/ninetynine/tests/ -v
```

### O que NÃO está neste PR

- OAuth / renovação de token 99Food (próximo PR)
- Atualização de status de pedido via webhook (só criação)
- Open Delivery: outros marketplaces (Rappi, Uber Eats) — mesmo padrão, ~2h cada
- Reconciliação financeira
- Cancelamento automático via API

## KDS — Kitchen Display System (PR 5)

### Endpoints

| Método | Endpoint | Descrição | Acesso |
|--------|----------|-----------|--------|
| GET | `/api/v1/kds/stations/` | Listar estações da store | Autenticado |
| POST | `/api/v1/kds/stations/` | Criar estação | Autenticado |
| PATCH | `/api/v1/kds/stations/{id}/` | Atualizar estação | Autenticado |
| DELETE | `/api/v1/kds/stations/{id}/` | Remover estação | Autenticado |
| GET | `/api/v1/kds/stations/{id}/tickets/` | Pedidos ativos (polling) | Autenticado |
| GET | `/api/v1/kds/stations/{id}/tickets/?include_done=true` | Incluir finalizados | Autenticado |
| GET | `/api/v1/kds/stations/{id}/metrics/` | Tempo médio de preparo (24h) | Autenticado |
| GET | `/api/v1/kds/tickets/{id}/` | Detalhar ticket | Autenticado |
| PATCH | `/api/v1/kds/tickets/{id}/status/` | Avançar status do ticket | Autenticado |

### Estados do Ticket KDS

```
WAITING → IN_PROGRESS → DONE
WAITING → DONE (skip direto permitido)
```

### Como funciona

- Quando Order vai para CONFIRMED, signal cria KDSTicket em todas as estações ativas da store
- Estações podem filtrar por order_type (ex: só delivery, só mesa)
- Frontend faz polling em `/kds/stations/{id}/tickets/` (recomendado: a cada 5s)
- `elapsed_seconds` no ticket permite exibir timer em tempo real no frontend

### Rodar testes do PR 5

```bash
cd apps/api
pytest kds/tests/ -v
```

### O que NÃO está neste PR

- WebSocket / tempo real push (polling é suficiente para MVP)
- Impressão de comanda
- Priorização manual de tickets
- KDS por item (granularidade de item, não pedido)
- Notificações sonoras (frontend)
- Histórico avançado / relatórios KDS

## Catálogo (PR 6)

### Endpoints

```
# Catálogos
GET    /api/v1/catalogs/
POST   /api/v1/catalogs/
GET    /api/v1/catalogs/{id}/
PATCH  /api/v1/catalogs/{id}/
DELETE /api/v1/catalogs/{id}/
GET    /api/v1/catalogs/{id}/public/      ← sem autenticação, canal próprio

# Categorias (aninhado)
GET    /api/v1/catalogs/{id}/categories/
POST   /api/v1/catalogs/{id}/categories/

# Produtos (aninhado)
GET    /api/v1/catalogs/{cid}/categories/{catid}/products/
POST   /api/v1/catalogs/{cid}/categories/{catid}/products/
GET    /api/v1/catalogs/{cid}/categories/{catid}/products/{pid}/
GET    /api/v1/catalogs/{cid}/categories/{catid}/products/available/?channel=IFOOD

# Mapeamento por canal (aninhado)
GET    /api/v1/catalogs/{cid}/categories/{catid}/products/{pid}/channel-maps/
POST   /api/v1/catalogs/{cid}/categories/{catid}/products/{pid}/channel-maps/
```

### Hierarquia

```
Catalog → Category → Product → ModifierGroup → ModifierOption
                             → ProductChannelMap  (ID externo por canal)
                             → ProductAvailability (horário por dia da semana)
```

### Rodar testes do PR 6

```bash
cd apps/api
pytest catalog/tests/ -v
```

### O que NÃO está neste PR

- Push de cardápio para iFood (sincronização) — PR futuro
- Estoque vinculado a produto
- Precificação dinâmica / promoções
- Catálogo por horário (schedule de catálogo inteiro)
- Imagens com upload (image_url é campo de texto — CDN externo)
- Importação de cardápio via CSV/planilha

## CDP — Customer Data Platform (PR 7)

### Endpoints

```
GET    /api/v1/customers/                        → listar clientes do tenant
POST   /api/v1/customers/                        → criar cliente
GET    /api/v1/customers/{id}/                   → perfil + RFV + consent_summary
PATCH  /api/v1/customers/{id}/                   → atualizar dados
GET    /api/v1/customers/{id}/events/            → histórico de eventos
GET    /api/v1/customers/{id}/consents/          → histórico de consentimentos
POST   /api/v1/customers/{id}/consent/           → grant ou revoke consentimento
POST   /api/v1/customers/{id}/trigger-rfv/       → recalcular RFV (admin/debug)
```

### RFV (Recência, Frequência, Valor)

- Calculado assincronamente via Celery quando Order -> DELIVERED
- `rfv_recency_days` — dias desde último pedido entregue
- `rfv_frequency` — total de pedidos entregues
- `rfv_monetary_cents` — valor total gasto

### Consentimento LGPD

- Append-only: cada grant/revoke cria um novo registro (nunca edita/deleta)
- Status atual = registro mais recente por (customer, channel)
- Canais: WHATSAPP, EMAIL, SMS, PUSH

### Rodar testes do PR 7

```bash
cd apps/api
pytest cdp/tests/ -v
```

### O que NÃO está neste PR

- Campanhas / automações de CRM (PR 8)
- Disparos de WhatsApp / email / SMS
- Segmentação de clientes por RFV
- Order com FK para Customer (vínculo direto — roadmap)
- Verificação de telefone / email (OTP)
- Merge de perfis duplicados

## CRM MVP (PR 8)

### Endpoints

```
# Segmentos
GET    /api/v1/crm/segments/                   → listar segmentos
POST   /api/v1/crm/segments/                   → criar segmento
GET    /api/v1/crm/segments/{id}/preview/      → preview: tamanho + amostra

# Templates
GET    /api/v1/crm/templates/
POST   /api/v1/crm/templates/

# Campanhas
GET    /api/v1/crm/campaigns/
POST   /api/v1/crm/campaigns/
POST   /api/v1/crm/campaigns/{id}/launch/      → disparar campanha
GET    /api/v1/crm/campaigns/{id}/runs/        → histórico de execuções

# Billing
GET    /api/v1/crm/billing/quota/              → teto de contatos e uso atual
```

### Critérios de segmento disponíveis

| Critério | Parâmetro | Exemplo |
|---|---|---|
| `ALL_CUSTOMERS` | — | todos os clientes ativos |
| `RFV_RECENCY_LTE` | dias | clientes com pedido nos últimos 30 dias |
| `RFV_FREQUENCY_GTE` | pedidos | clientes com 5+ pedidos |
| `RFV_MONETARY_GTE` | centavos | clientes que gastaram R$100+ |
| `NO_ORDER_SINCE_DAYS` | dias | win-back: sem pedido há 30+ dias |
| `HAS_CONSENT` | canal | tem consentimento WHATSAPP |

### Billing — diferencial vs Repediu

- Teto configurado por tenant
- Alerta automático em 80% de uso
- **BLOQUEIO com mensagem clara em 100%**
- **Nunca upgrade automático silencioso**

### Rodar testes do PR 8

```bash
cd apps/api
pytest crm/tests/ -v
```

### O que NÃO está neste PR

- Adapters reais (Twilio, SendGrid, etc.) — stub apenas
- Agendamento automático de campanhas (Celery Beat) — lançamento é manual
- Tracking de abertura / clique (pixel, link curto)
- A/B testing de templates
- Fluxos de automação (ex: 3 dias sem pedir → disparar campanha)
- Relatórios avançados de campanha
- Upgrade de plano via API (manual via painel)

## Estoque Pro (PR 9)

### Endpoints

```
# Itens de estoque
GET    /api/v1/stock/items/                    → listar itens da store
POST   /api/v1/stock/items/                    → criar item
GET    /api/v1/stock/items/{id}/               → detalhar (com saldo atual)
PATCH  /api/v1/stock/items/{id}/               → atualizar item
DELETE /api/v1/stock/items/{id}/               → remover item
GET    /api/v1/stock/items/{id}/movements/     → movimentos do item
POST   /api/v1/stock/items/{id}/recalculate/   → forçar recálculo (admin)

# Movimentos (append-only)
GET    /api/v1/stock/movements/                → listar movimentos da store
POST   /api/v1/stock/movements/                → registrar entrada/saída

# Alertas de estoque baixo
GET    /api/v1/stock/alerts/                   → alertas abertos (default)
GET    /api/v1/stock/alerts/?open=false        → todos (abertos + resolvidos)
POST   /api/v1/stock/alerts/{id}/resolve/      → resolver alerta manualmente

# Ficha técnica (BOM)
GET    /api/v1/stock/bom/                      → listar fichas técnicas
POST   /api/v1/stock/bom/                      → criar ficha técnica
PATCH  /api/v1/stock/bom/{id}/                 → atualizar quantidade
DELETE /api/v1/stock/bom/{id}/                 → remover ficha técnica
```

### Tipos de movimento

| Tipo | Descrição | Quantidade |
|---|---|---|
| `ENTRADA` | Compra, recebimento | Positiva |
| `SAIDA` | Consumo, venda | Negativa (normalizado) |
| `AJUSTE` | Correção manual | Positiva ou negativa |
| `PERDA` | Desperdício, vencimento | Negativa |
| `INVENTARIO` | Contagem física | Positiva ou negativa |

### Débito automático (Order → DELIVERED)

Quando um pedido é entregue, signal dispara task Celery que:
1. Busca `BillOfMaterials` via `ProductChannelMap.external_id` ↔ `OrderItem.external_item_id`
2. Cria `StockMovement` (SAIDA) para cada insumo consumido
3. Recalcula `StockLevel` e gera `StockAlert` se abaixo do mínimo
4. Idempotente: verifica `reference_type='order'` antes de debitar

### Rodar testes do PR 9

```bash
cd apps/api
pytest stock/tests/ -v
```

### O que NÃO está neste PR

- Contagem de inventário via mobile (barcode scan)
- Compras e NF-e (entrada automatizada)
- Custo médio / FIFO / LIFO
- Relatórios de consumo e desperdício
- Transferência entre lojas
- Previsão de demanda

## Enterprise — Franquias (PR 10)

### Endpoints

```
# Template da rede
GET    /api/v1/enterprise/templates/
POST   /api/v1/enterprise/templates/
POST   /api/v1/enterprise/templates/{id}/onboard-store/   → provisionar nova store

# Overrides por store
GET    /api/v1/enterprise/overrides/
POST   /api/v1/enterprise/overrides/

# Onboardings
GET    /api/v1/enterprise/onboardings/
POST   /api/v1/enterprise/onboardings/{id}/retry/         → retentar onboarding falho

# Relatórios da rede
GET    /api/v1/enterprise/reports/
POST   /api/v1/enterprise/reports/generate/               → gerar relatório (async)

# Alertas da rede
GET    /api/v1/enterprise/alerts/                         → alertas abertos (?open=false)
POST   /api/v1/enterprise/alerts/{id}/resolve/
POST   /api/v1/enterprise/alerts/check/                   → verificar alertas manualmente
```

### Fluxo de onboarding de nova store

```
1. POST /enterprise/templates/{id}/onboard-store/ {"store_id": "..."}
2. → FranchiseeOnboarding criado (PENDING)
3. → run_franchisee_onboarding.delay() enfileirado
4. Steps executados (idempotente):
   - copy_catalog       → copia catálogo base com produtos
   - copy_kds_stations  → cria estações KDS padrão
   - copy_bom           → copia fichas técnicas
   - create_billing_quota → cria quota CRM
   - create_store_override → cria override vazio (herda tudo)
5. Status: DONE
```

### Rodar testes do PR 10

```bash
cd apps/api
pytest enterprise/tests/ -v
```

### O que NÃO está neste PR

- Royalties / financeiro da franquia
- Portal web do franqueado
- Aprovação de override pela rede (workflow de aprovação)
- Sincronização de cardápio em tempo real entre stores
- Benchmarking automático de performance entre stores

## Admin Panel

Acesse: http://localhost:8000/admin/

### Criar superuser

```bash
cd apps/api
python manage.py createsuperuser
```

### Painéis disponíveis

| App | O que você pode fazer |
|---|---|
| **Tenants** | Ver tenants, companies, stores e memberships |
| **Orders** | Ver pedidos, cancelar em massa, ver itens inline |
| **iFood** | Monitor de eventos, reprocessar falhas |
| **99Food** | Credenciais por store |
| **KDS** | Ver estações e tickets ativos |
| **Catalog** | Gerenciar cardápio completo com modificadores |
| **CDP** | Perfis de clientes, RFV, consentimentos |
| **CRM** | Segmentos, campanhas, quota de billing |
| **Stock** | Itens, movimentos, alertas, BOM |
| **Enterprise** | Templates, overrides, onboardings, relatórios, alertas da rede |
| **Audit** | Eventos de auditoria (somente leitura) |

### Modelos append-only (sem edição/exclusão)

- `RawEvent` — eventos iFood / 99Food
- `StockMovement` — movimentos de estoque
- `ConsentRecord` — consentimentos LGPD
- `CustomerEvent` — eventos do cliente
- `AuditEvent` — auditoria

## Seed — Dados de Demo

### Rodar seed completo

```bash
cd apps/api
python manage.py seed
```

### Limpar e re-sedar

```bash
cd apps/api
python manage.py seed --clear
```

### O que é criado

- **2 tenants**: Burguer Palace (rede, 3 lojas) + Pizza Napoli (independente)
- **Catálogos completos** com modificadores e channel maps iFood
- **30 clientes** com RFV variado (VIPs, regulares, inativos, novos)
- **~90+ pedidos** nos últimos 90 dias (histórico realista)
- **Estoque** com 7 itens + 1 alerta de mínimo ativo
- **3 estações KDS** configuradas
- **3 segmentos CRM** + 1 campanha em rascunho

### Credenciais de demo

| Email | Senha | Role |
|---|---|---|
| `owner@burguerpala.ce` | `demo123` | Owner (Burguer Palace) |
| `manager.paulista@burguerpala.ce` | `demo123` | Manager (Paulista) |
