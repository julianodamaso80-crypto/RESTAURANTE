# Backlog 1.0

## Estratégia de execução
- Construir por PRs pequenos, cada PR com testes e documentação.
- Ordem: Fundacao SaaS, Modelo de pedidos, Fila e observabilidade, iFood, KDS, Catálogo, CDP, CRM, Estoque, Enterprise.

## PRs planejados
PR 1 ✅
- Épico A: Fundacao SaaS (A1 a A3)

PR 2 ✅
- Épico B: Modelo interno de pedidos (somente schema e estados)

PR 3 ✅
- Épico C: Fila, worker e observabilidade mínima

PR 4 ✅
- Épico D: Conector iFood MVP (webhook + assinatura + enqueue + retry controlado)

PR 5 ✅
- Épico E: KDS básico (estações, tickets, métricas, signal)

## Épicos

Épico A: Fundacao SaaS multi-tenant ✅
- A1 Modelos: tenant, empresa, loja, usuário, memberships ✅
- A2 RBAC: roles e permissions por escopo (tenant, empresa, loja) ✅
- A3 Auditoria: trilha de ações para mudanças críticas ✅

Épico B: Modelo interno de pedidos ✅
- B1 Schema interno e estados ✅
- B2 Idempotência e deduplicação ✅
- B3 Evento bruto e normalizado ✅

Épico C: Pipeline de eventos e filas ✅
- C1 Fila e worker ✅
- C2 Reprocessamento
- C3 Dashboard de saúde por loja e conector

Épico D: Conector iFood MVP ✅
- D1 Webhook com validação de assinatura X-IFood-Signature ✅
- D2 Resposta 202 rápida e processamento assíncrono ✅
- D3 Hydration com retry 404 pós criação e backoff controlado ✅
- D4 Health por loja e reprocessamento ✅

Épico E: KDS e operação ✅ (MVP)
- E1 KDS com colunas por status ✅
- E2 Alertas e prioridades (roadmap — métricas de tempo implementadas)
- E3 Impressão opcional

Épico F: Catálogo e mapeamento por canal
- F1 CRUD catálogo e modificadores
- F2 Mapeamento para iFood
- F3 Agenda de disponibilidade

Épico G: CDP
- G1 Perfil unificado e RFV
- G2 Consentimento e opt-in
- G3 Segmentos salvos

Épico H: CRM
- H1 Pós-compra com cupom
- H2 Reativação 30 dias
- H3 Métricas de impacto

Épico I: Estoque Pro
- I1 Insumos e ficha técnica
- I2 Compras e fornecedores

Épico J: Enterprise franquias
- J1 Hierarquia e governança
- J2 Catálogo central com exceções
- J3 Auditoria avançada e compliance
