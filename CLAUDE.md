# Instrucoes permanentes do projeto

Leia sempre antes de codar
- docs/PRD.md
- docs/BACKLOG.md
- docs/RULES.md

Como trabalhar
- Sempre quebrar em tarefas pequenas e entregar com testes.
- Nunca inventar requisitos. Se algo estiver ambíguo, registrar a dúvida como TODO no próprio PR e seguir o PRD.
- Manter logs estruturados e audit trail para ações críticas.

Arquitetura alvo
- SaaS multi-tenant com empresas e lojas.
- Núcleo de pedidos omnichannel com um modelo interno único.
- Conectores isolados por canal (iFood, 99Food, canal próprio).

Qualidade
- Sempre rodar lint e testes antes de finalizar.
- Atualizar README e docs quando mudar como rodar o projeto.
