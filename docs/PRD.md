# PRD 1.0 - ERP e SaaS omnichannel para restaurantes

## 1. Visão
Construir um sistema operacional do restaurante no Brasil: pedidos omnichannel, operação de cozinha, catálogo, estoque, financeiro e dados do cliente unificados (CDP) com automações (CRM). Vender como SaaS modular que atende do pequeno até redes e franquias.

## 2. Perfis de cliente
- Pequeno: 1 loja, precisa operar rápido e sem erro
- Médio: 2 a 10 lojas, quer padronizar e controlar
- Rede e franquia: governança, auditoria, catálogo central e métricas consolidadas

## 3. Objetivos
- Unificar pedidos de todos os canais em um fluxo único e confiável
- Reduzir erro operacional e tempo de preparo com KDS e regras
- Criar base própria de clientes com consentimento e segmentação
- Entregar relatórios e conciliação por canal com rastreabilidade

## 4. Módulos do produto

4.1 Núcleo SaaS
- Multi-tenant: tenant, empresa, loja
- Usuários, perfis e permissões (RBAC)
- Auditoria (quem fez o quê, quando e onde)
- Billing e limites por plano (teto de gasto, upgrade somente com aceite)

4.2 Hub de pedidos omnichannel
- Modelo interno único de pedido e estados
- Ingestão por eventos com idempotência e deduplicação
- Persistir evento bruto e normalizado
- Reprocessamento seguro por loja e por orderId

4.3 Operação e cozinha
- KDS por estações e status
- Tempo decorrido, alertas e prioridades
- Impressão opcional e registros

4.4 Catálogo
- Produtos, categorias, variações, adicionais, combos
- Regras de opcionais e substituições
- Agenda de disponibilidade por horário e dia
- Mapeamento por canal (IDs diferentes por marketplace)

4.5 Estoque e ficha técnica
- Insumos, ficha técnica e baixa automática
- Estoque mínimo e alertas
- Compras e fornecedores (fase Pro)

4.6 Financeiro
- Relatórios por canal, taxas e cancelamentos
- Conciliação com marketplaces (fase Pro e Enterprise)

4.7 CDP e CRM
- Perfil do cliente: histórico, frequência, ticket, preferências
- Consentimento e opt-in
- Segmentação RFV
- Jornadas: pós-compra, reativação, aniversário, abandono

4.8 Canal próprio
- Cardápio web e link de pedido
- Pagamento online opcional
- Cupons e fidelidade simples

## 5. Integração iFood (requisitos para homologação futura)
- Webhook: validar assinatura X-IFood-Signature e rejeitar inválidas.
- Responder 202 rapidamente e processar assíncrono via fila.
- Entrega pode repetir e não garante ordem: idempotência e deduplicação obrigatórias.
- Se buscar detalhes do pedido e receber 404 logo após evento de criação, aplicar retry com exponential backoff por janela limitada, sem retry infinito.

## 6. Integração 99Food
- Implementar como plugin isolado, sempre adaptando para o mesmo modelo interno de pedido e catálogo.
- Nunca acoplar o core ao conector.

## 7. Planos
Starter
- Hub de pedidos, KDS básico, catálogo, conector iFood básico no futuro

Pro
- Multi-loja, estoque simples, CRM básico, canal próprio

Enterprise
- Governança de franquias, auditoria avançada, conciliação avançada, permissões granulares

## 8. Requisitos não funcionais
- Segurança: RBAC, logs estruturados, trilha de auditoria, proteção de secrets
- Confiabilidade: filas, retries controlados, idempotência, reprocessamento
- Observabilidade: métricas por loja e por conector, alertas
- Performance: endpoints críticos com baixa latência e sem trabalho pesado síncrono

## 9. KPIs iniciais
- Pedidos processados por canal e taxa de falha por conector
- Tempo médio de preparação e atraso por estação
- Taxa de recompra e churn de clientes
- Receita por canal e margem estimada
