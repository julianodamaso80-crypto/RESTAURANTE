# DECISIONS.md — Architecture Decision Records

> Formato: [ID] Título | Status | Decisão | Razão | Consequências

---

## ADR-001 — Stack principal

**Status:** ✅ IMPLEMENTADO (PR 0 / PR 1)

**Decisão:**
- Backend: Python 3.12 + Django 5.x + Django REST Framework
- Banco: PostgreSQL 16
- Cache/Fila: Redis 7 + Celery 5
- Testes: Pytest + pytest-django + factory_boy
- Containerização: Docker Compose (dev) / imagem única (prod)

**Razão:** Ecossistema maduro, vasto em libraries para multi-tenant, auditoria e integrações. Django ORM simplifica migrations versionadas.

**Consequências:** Celery obrigatório para qualquer processamento assíncrono (nenhum endpoint crítico faz trabalho pesado síncrono).

---

## ADR-002 — Autenticação

**Status:** ✅ IMPLEMENTADO (PR 1)

**Decisão:** JWT via `djangorestframework-simplejwt`.
- Access token: 15 min
- Refresh token: 7 dias
- Rotação de refresh habilitada

**Razão:** Stateless, compatível com múltiplos frontends (web, mobile, integrador externo).

**Consequências:** Nenhum estado de sessão no servidor. Logout = blacklist do refresh token (tabela `TokenBlacklist`).

---

## ADR-003 — Multi-tenant

**Status:** ✅ IMPLEMENTADO (PR 1)

**Decisão:** Schema único (shared schema), isolamento por FK obrigatória em todos os models.

Hierarquia:
```
Tenant (cliente SaaS)
  └── Company (empresa / CNPJ)
        └── Store (loja física ou virtual)
```

Escopo no request via headers:
- `X-Tenant-ID` (obrigatório)
- `X-Store-ID` (opcional, quando operação é por loja)

**Razão:** Simples de manter, queries sempre filtradas. Alternativa (schema por tenant) adiciona complexidade de migrations desnecessária neste estágio.

**Consequências:**
- Todo model de domínio DEVE ter FK para `Store` ou `Tenant` (nunca orphan).
- Middleware de escopo valida e injeta `request.tenant` e `request.store` em todo request autenticado.
- Queries sem filtro de tenant são proibidas fora de admin/superuser.

---

## ADR-004 — RBAC (Controle de Acesso)

**Status:** ✅ IMPLEMENTADO (PR 1)

**Decisão:** Papéis definidos por `Membership` (User → Store/Company com role).

Roles mínimas:
- `owner` → acesso total ao tenant
- `manager` → acesso à store, sem billing/configuração de tenant
- `operator` → acesso operacional (pedidos, KDS, caixa)
- `readonly` → somente leitura

**Razão:** Granularidade suficiente para PME e franquias sem over-engineering.

**Consequências:** Permissões checadas via decorator/mixin DRF em todo endpoint. Superuser Django reservado para suporte interno.

---

## ADR-005 — Auditoria

**Status:** ✅ IMPLEMENTADO (PR 1)

**Decisão:** Model `AuditEvent` com campos:
```
tenant, store, user, action, resource_type, resource_id,
payload (JSONField), ip_address, user_agent, created_at
```

Gravado via signal ou mixin em toda operação de escrita relevante.

**Razão:** Requisito de rastreabilidade para franquias e compliance fiscal.

**Consequências:** `AuditEvent` é append-only. Nenhum registro pode ser deletado ou editado via API. Retenção: 2 anos (configurável por tenant).

---

## ADR-006 — Logs estruturados

**Status:** ✅ IMPLEMENTADO (PR 3)

**Decisão:**
- Formato: JSON em produção, texto legível em dev
- Campos obrigatórios em todo log: `timestamp`, `level`, `request_id`, `correlation_id`, `tenant_id`, `store_id` (quando aplicável), `message`
- `request_id`: UUID gerado no início de cada request HTTP
- `correlation_id`: UUID propagado entre serviços/workers (header `X-Correlation-ID`)
- Library: `structlog` configurado no Django settings

**Critério de aceite:** Todo log de request e worker contém os 6 campos obrigatórios. Validado por teste de integração.

---

## ADR-007 — Eventos externos (webhooks e integrações)

**Status:** ✅ IMPLEMENTADO (PR 4)

**Decisão:**

Pipeline obrigatório para qualquer evento externo:
```
1. Validar assinatura/autenticidade
2. Persistir evento bruto (RawEvent) → imediatamente
3. Responder 2xx ao caller → imediatamente (< 2s)
4. Enqueue tarefa Celery
5. Processar assincronamente
6. Checar idempotency key antes de processar
7. Deduplicate (marcar como processed/duplicate)
8. Permitir reprocessamento manual via admin
```

Nenhum endpoint de webhook faz trabalho pesado síncrono. **Inegociável.**

**Critério de aceite:** Teste que simula evento duplicado e prova que é processado apenas uma vez.

---

## ADR-008 — Modelo interno de Pedido (Order)

**Status:** ✅ IMPLEMENTADO (PR 2)

**Decisão:**

- Model `Order` é o modelo canônico interno → independente de canal/marketplace.
- Toda integração (iFood, 99Food, canal próprio) mapeia para `Order` via adapter.
- Estados da máquina (FSM):

```
PENDING → CONFIRMED → IN_PREPARATION → READY → DISPATCHED → DELIVERED
                                                            → CANCELLED (de qualquer estado anterior a DELIVERED)
         → CANCELLED
```

- Transições inválidas devem levantar exceção explícita (não silenciar).
- `IdempotencyKey` model para garantir que eventos externos não criem pedidos duplicados.

**Critério de aceite:** Testes cobrem todas as transições válidas e todas as inválidas.

---

## ADR-009 — Billing e limites

**Status:** ⚠️ PARCIAL — quota de contatos CRM implementada (PR 8), billing completo: TODO

**Decisão (planejada):**
- Teto de uso configurado por tenant com alertas em 80% e 100%.
- Upgrade de plano somente com aceite explícito (nunca automático sem notificação).
- Diferencial vs Repediu: sem upgrade surpresa.
- PR 8: `TenantBillingQuota` + `check_and_consume_quota()` implementados para contatos CRM.

---

## ADR-010 — Integrações de marketplace (iFood, 99Food, Open Delivery)

**Status:** ⚠️ PARCIAL — iFood implementado (PR 4), 99Food e Open Delivery: TODO

**Decisão:**
- Cada marketplace é um adapter isolado que implementa interface `MarketplaceAdapter`.
- O core do ERP nunca importa diretamente código de marketplace específico.
- iFood: autenticação centralizada + webhook com validação `X-IFood-Signature` obrigatória.
- 99Food: adapter isolado, falha do adapter não afeta core.
- Open Delivery: adapter padronizado como acelerador de novas integrações.

---

## ADR-011 — KDS: polling vs WebSocket

**Status:** ✅ IMPLEMENTADO (PR 5) — polling

**Decisão:** MVP usa polling HTTP (frontend chama `/kds/stations/{id}/tickets/` a cada ~5s).
WebSocket (Django Channels) será avaliado no PR futuro quando tivermos métrica de carga real.

**Razão:** Simples de implementar e operar. Para restaurantes com até 100 pedidos/hora,
polling a cada 5s gera carga trivial. WebSocket adiciona complexidade de infra (channel layer, Redis pub/sub).

**Critério para reavaliar:** > 50 clientes KDS simultâneos por store OU latência de polling > 2s.

---

## ADR-012 — Catálogo: OrderItem como snapshot (sem FK para Product)

**Status:** ✅ IMPLEMENTADO (PR 6) — decisão mantida do PR 2

**Decisão:** OrderItem armazena nome, preço e external_item_id como campos de texto.
Não há FK de OrderItem para Product.

**Razão:** Cardápio muda (preço, nome, disponibilidade). Um pedido histórico deve refletir
o estado do cardápio no momento da compra, não o estado atual.

**Consequências:** Relatórios históricos são precisos. Para buscar o produto atual de um
OrderItem, usa-se ProductChannelMap.external_item_id como chave de lookup — não FK direta.

---

## ADR-013 — CDP: Customer por Tenant, não por Store

**Status:** ✅ IMPLEMENTADO (PR 7)

**Decisão:** `Customer` é vinculado a `Tenant`, não a `Store`.
O mesmo cliente que pede na Loja A e na Loja B da mesma rede é UM Customer.

**Razão:** Permite visão unificada de RFV e histórico do cliente em toda a rede.
Fundamental para franquias e redes multi-loja.

**Consequências:** Eventos de Customer registram a Store onde ocorreram.
Order não tem FK para Customer ainda — vínculo é feito via CustomerIdentity (PR futuro: Order terá campo customer_phone/customer_id).

---

## ADR-014 — Consentimento LGPD: append-only

**Status:** ✅ IMPLEMENTADO (PR 7)

**Decisão:** `ConsentRecord` é append-only. Nenhum registro pode ser editado ou deletado via API.
O consentimento atual é sempre o registro mais recente por (customer, channel).

**Razão:** Compliance LGPD exige histórico auditável de quando o consentimento foi dado e revogado.

**Consequências:** Relatórios de consentimento podem consultar o histórico completo.
Retenção: indefinida (dados de compliance).

---

## ADR-015 — RFV: cálculo assíncrono, nunca síncrono

**Status:** ✅ IMPLEMENTADO (PR 7)

**Decisão:** RFV sempre calculado via Celery task (`recalculate_customer_rfv.delay()`).
Nunca calculado no request, nunca calculado no signal de forma síncrona.

**Razão:** RFV pode envolver queries pesadas em tenants grandes. Signal dispara `.delay()` — retorna imediatamente.

**Critério para reavaliar:** Se latência da task > 30s para tenants grandes, migrar para
cálculo incremental (atualizar delta ao invés de recalcular tudo).

---

## ADR-016 — CRM: adapter pattern para canais de comunicação

**Status:** ✅ IMPLEMENTADO (PR 8) — StubChannelAdapter

**Decisão:** Canais de comunicação (WhatsApp, email, SMS) implementados como adapters
intercambiáveis via `BaseChannelAdapter`. MVP usa `StubChannelAdapter` (só loga).

**Razão:** Evita acoplamento com provider específico. Trocar Twilio por outro provider
= implementar novo adapter, não tocar em tasks/models.

**Para produção:** Implementar `TwilioAdapter`, `SendGridAdapter`, etc. e registrar
em `get_adapter()` por canal.

---

## ADR-017 — Billing: teto explícito sem upgrade automático

**Status:** ✅ IMPLEMENTADO (PR 8)

**Decisão:** `check_and_consume_quota()` bloqueia (levanta `QuotaExceeded`) quando
`current + quantity > max`. Nunca altera `max_contacts` automaticamente.

**Razão:** Diferencial competitivo vs Repediu (que faz upgrade automático na próxima fatura).
Transparência e confiança do cliente.

**Consequências:** Tenant bloqueado precisa acessar o painel e fazer upgrade manualmente
com aceite explícito. Endpoint `/billing/quota/` mostra status em tempo real.

---

## ADR-018 — Estoque: StockMovement append-only, StockLevel desnormalizado

**Status:** ✅ IMPLEMENTADO (PR 9)

**Decisão:** `StockMovement` é append-only (fonte da verdade). `StockLevel` é uma tabela
desnormalizada recalculada assincronamente (Celery) após cada movimento.

Fluxo:
```
1. Criar StockMovement (positivo=entrada, negativo=saída)
2. .delay(recalculate_stock_level)
3. Task soma todos os movimentos → atualiza StockLevel
4. Se saldo < mínimo → cria StockAlert
5. Se saldo voltou ao normal → resolve alertas abertos
```

**Razão:** Append-only garante rastreabilidade total (auditoria). Desnormalização via task
evita queries pesadas em cada leitura de saldo. Recálculo idempotente via SUM(movements).

**Consequências:**
- StockLevel pode estar momentaneamente desatualizado (eventual consistency).
- Endpoint `POST /stock/items/{id}/recalculate/` permite forçar recálculo manual (admin/debug).
- StockMovement não pode ser editado ou deletado via API.

---

## ADR-019 — BOM: lookup via ProductChannelMap.external_id

**Status:** ✅ IMPLEMENTADO (PR 9)

**Decisão:** `BillOfMaterials` (ficha técnica) liga `catalog.Product` → `stock.StockItem`.
Quando um pedido é entregue, o débito automático encontra o BOM via:

```
BillOfMaterials.objects.filter(
    product__channel_maps__external_id=order_item.external_item_id,
    is_active=True,
)
```

**Razão:** `OrderItem` não tem FK para `Product` (ADR-012). O campo `external_item_id` no
`OrderItem` é o snapshot do ID no marketplace. `ProductChannelMap.external_id` faz o link.

**Consequências:**
- Débito automático depende de `ProductChannelMap` estar configurado.
- Itens sem `external_item_id` são ignorados (sem BOM match).
- Débito é idempotente: verifica `reference_type='order'` + `reference_id` antes de criar.

---

## ADR-020 — Enterprise: herança por override aditivo

**Status:** ✅ IMPLEMENTADO (PR 10)

**Decisão:** Store herda tudo do FranchiseTemplate por padrão.
StoreOverride é aditivo — só sobrescreve o que a store precisa mudar.
Sem herança complexa de classes — simples dicts JSON de override.

**Razão:** Franquias precisam de flexibilidade (preço regional, produto local indisponível)
sem perder a padronização da rede. JSON de override é simples, auditável e extensível.

**Consequências:**
- Override vazio = store herda 100% do template.
- Métodos `get_product_price()` e `is_product_active()` no StoreOverride centralizam a lógica.
- Novos campos de override podem ser adicionados ao JSON sem migration.

---

## ADR-021 — Onboarding: idempotente via steps_completed

**Status:** ✅ IMPLEMENTADO (PR 10)

**Decisão:** FranchiseeOnboarding registra steps_completed como lista JSON.
Cada step usa get_or_create — pode ser executado múltiplas vezes sem duplicar dados.
Em caso de falha, onboarding pode ser retentado do ponto onde parou.

**Razão:** Onboarding de store envolve múltiplos steps com risco de falha parcial.
Idempotência garante que retry seguro não gera dados inconsistentes.

**Consequências:**
- Retry via `POST /enterprise/onboardings/{id}/retry/` é seguro.
- Steps já concluídos são pulados no re-run.
- unique_together (template, store) previne duplicação de onboarding.

---

*Última atualização: PR 10 — próxima revisão obrigatória no PR 11.*
