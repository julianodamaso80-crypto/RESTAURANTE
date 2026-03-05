# Como conectar o 99Food no MesaMestre

## Encontrando seu AppShopID no 99Food

1. Acesse o **Painel de Gestao do 99Food**
2. Va em **Configuracoes > Integracao** (ou API)
3. Copie o **AppShopID** (codigo numerico ou alfanumerico)
4. Cole no MesaMestre em **Integracoes > Conectar 99Food**

## O que e o AppShopID?

E o identificador unico da sua loja no 99Food.
E usado como chave de autenticacao para que o MesaMestre
receba seus pedidos automaticamente.

**Importante:** O AppShopID e confidencial. Nao compartilhe
com terceiros alem do MesaMestre.

## Fluxo de conexao

1. No MesaMestre, va em **Integracoes**
2. Clique em **Conectar 99Food**
3. Informe o **AppShopID** e opcionalmente o nome da loja
4. O sistema valida as credenciais contra a API do 99Food
5. Se valido, a conexao e salva e o polling de pedidos inicia automaticamente
6. Pedidos do 99Food aparecerão no painel de pedidos do MesaMestre

## Desconectando

1. No MesaMestre, va em **Integracoes**
2. Clique em **Desconectar 99Food**
3. A credencial sera desativada e o polling interrompido

## Diferenca entre iFood e 99Food

| | iFood | 99Food |
|---|---|---|
| Conexao | OAuth (redirecionamento) | Manual (AppShopID) |
| Autenticacao | Authorization Code Flow | Client Credentials |
| Polling | Automatico a cada 30s | Automatico a cada 30s |
| Pipeline de pedidos | Identico | Identico |
