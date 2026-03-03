# Regras do projeto

## 1. Regras de entrega
- Um PR por vez, escopo pequeno, sempre com testes.
- Não implementar épicos fora do PR planejado.
- Atualizar README e docs quando mudar setup ou arquitetura.

## 2. Segurança e acesso
- Todo endpoint deve exigir autenticação.
- RBAC obrigatório em endpoints e ações críticas.
- Logs estruturados em JSON, com correlation id por request.
- Nunca commitar secrets. Usar .env e .env.example.

## 3. Arquitetura de integrações
- Toda integração externa deve ser assíncrona via fila.
- Idempotência e deduplicação obrigatórias, pois eventos podem repetir e chegar fora de ordem.
- Reprocessamento sempre disponível, por loja e por entidade.

## 4. Regras específicas iFood para quando for implementado
- Webhook deve validar o header X-IFood-Signature e rejeitar assinaturas inválidas.
- Webhook deve responder 202 rapidamente e enfileirar evento para processamento posterior.
- Nunca fazer chamadas externas antes de responder 202.
- Timeout do webhook é curto, então qualquer tarefa pesada deve ser no worker.
- Implementar retry controlado com exponential backoff para casos transitórios, com janela máxima e sem retry infinito.

## 5. Qualidade
- Lint e testes obrigatórios.
- Migrations versionadas.
- Cobertura mínima para regras de auth, RBAC e auditoria.

## 6. Decisões do projeto

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| User model | `AbstractBaseUser` + `PermissionsMixin` | Login por email, sem campo username |
| Primary keys | `UUIDField` em todos os modelos | Segurança e multi-tenant friendly |
| JWT library | `djangorestframework-simplejwt` | Padrão de mercado, boa integração com DRF |
| Filtros | `django-filter` | Padrão para filtros no DRF |
| Auditoria | `AuditMixin` em ViewSets | Acesso direto ao request para capturar metadata |
| Banco testes | SQLite | Velocidade nos testes sem depender de Docker |
| Membership constraints | `UniqueConstraint` com `condition` | Trata nulls corretamente em company e store |
| Scope middleware | Headers `X-Store-Id`, `X-Company-Id`, `X-Tenant-Id` | Resolve automaticamente a hierarquia de escopo |
| Escopo hierárquico | Store > Company > Tenant | Binding no tenant concede acesso a tudo abaixo |
| Admin-only tenants | `IsAdminUser` (superuser) | Tenants gerenciados apenas pelo admin da plataforma |
| Permissions format | `domain:action` (ex: `stores:read`) | Simples, previsível e fácil de filtrar |
| API format | JSON only | DRF configurado com `JSONParser` e `JSONRenderer` exclusivos |
