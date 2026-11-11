# Kalodata MCP Server (TikTok Shop Analytics)

Servidor MCP (**Model Context Protocol**) construído em Python com o SDK oficial (`FastMCP` v1.x). Funciona como um wrapper completo para a **Kalodata Open API**, permitindo que assistentes e agentes de IA (como **Perplexity AI**, Claude, Cursor e outros) realizem pesquisas aprofundadas de mercado, análise de nichos, produtos vencedores, criadores e vídeos virais do TikTok Shop.

---

## 📌 O que é este projeto?

Este servidor expõe 8 ferramentas MCP para consulta de dados do TikTok Shop:

1. `category_rank` — Ranking de categorias por receita.
2. `category_detail` — Detalhes completos de uma categoria.
3. `product_rank` — Ranking dos produtos mais vendidos.
4. `product_detail` — Detalhes e métricas de um produto.
5. `creator_rank` — Ranking de criadores/influenciadores.
6. `creator_detail` — Detalhes e performance de um criador.
7. `video_rank` — Ranking de vídeos virais de vendas.
8. `video_detail` — Métricas de um vídeo específico.

Transporte nativo: **Streamable HTTP** na rota `/mcp`, compatível com Perplexity AI Custom Remote Connectors.

---

## 🚀 Setup Local

### 1. Pré-requisitos
- Python 3.10 ou superior.
- Chave de API Kalodata (`KALODATA_SECRET_KEY`).

### 2. Ambiente Virtual e Dependências

```bash
python -m venv .venv

# Ativar (Windows PowerShell):
.venv\Scripts\Activate.ps1
# Ativar (Linux/macOS):
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Configurar `.env`

```bash
cp .env.example .env
```

Edite `.env`:
```env
KALODATA_SECRET_KEY=sua_chave_aqui
KALODATA_BASE_URL=https://staging.kalodata.com
PORT=8000
HOST=0.0.0.0
```

> **Nota**: Se sua chave for de **produção**, altere `KALODATA_BASE_URL` para o host fornecido no e-mail de ativação da Kalodata.

---

## 🧪 Testes e Validação Local

### 1. Testar conexão direta com a API Kalodata (sem MCP)

```bash
python test_local.py
```

### 2. Iniciar o servidor MCP

```bash
python server.py
```

Saída esperada nos logs:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
[kalodata-mcp] Servidor iniciando em http://0.0.0.0:8000/mcp
[kalodata-mcp] Transporte: streamable-http | 8 ferramentas registradas
```

### 3. Testar o endpoint `/mcp` via linha de comando

O endpoint correto é **`/mcp`** (testado e confirmado localmente com HTTP 200).

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri http://localhost:8000/mcp `
  -Method POST `
  -Headers @{"Accept"="application/json, text/event-stream"; "Content-Type"="application/json"} `
  -Body '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' `
  -UseBasicParsing | Select-Object -ExpandProperty Content
```

**Linux/macOS (curl):**
```bash
curl -s -N \
  -H "Accept: application/json, text/event-stream" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
  http://localhost:8000/mcp
```

Resposta esperada:
```
event: message
data: {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05","serverInfo":{"name":"kalodata","version":"1.29.1"},...}}
```

> **Importante**: O Streamable HTTP exige os dois headers `Accept: application/json, text/event-stream`. Sem eles, o servidor retorna 406 Not Acceptable (comportamento correto do protocolo).

### 4. Testar com MCP Inspector (interface visual)

```bash
npx @modelcontextprotocol/inspector python server.py
```

---

## 🌐 Deploy Remoto (Render.com)

O projeto já inclui o arquivo `render.yaml` na raiz, permitindo deploy via **Blueprint** no Render.

### Passo a Passo:

1. **Criar repositório no GitHub** e fazer push:
   ```bash
   git remote add origin https://github.com/seu-usuario/kalodata-mcp.git
   git push -u origin master
   ```

2. Acesse [dashboard.render.com](https://dashboard.render.com) → **New +** → **Blueprint**.

3. Conecte o repositório. O Render detecta o `render.yaml` automaticamente.

4. Configure as variáveis de ambiente manualmente no painel do Render:
   - `KALODATA_SECRET_KEY`: sua chave da Kalodata (rotacionada/nova)
   - `KALODATA_BASE_URL`: `https://staging.kalodata.com` (ou URL de produção)
   - `MCP_PATH_TOKEN`: código aleatório que vira parte da rota. Com ele, o endpoint passa a ser `/mcp/<MCP_PATH_TOKEN>` e `/mcp` responde 404, então só quem tem a URL completa usa seus créditos. Gere um com `python -c "import secrets; print(secrets.token_hex(24))"`.

5. Clique em **Apply**. O Render fará o build e gerará a URL pública (ex: `https://kalodata-mcp.onrender.com`).

6. Teste o deploy:
   ```bash
   curl -s -N \
     -H "Accept: application/json, text/event-stream" \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' \
     https://kalodata-mcp.onrender.com/mcp
   ```

---

## 🔗 Registrando no Perplexity AI

1. Acesse **Perplexity AI** → **Configurações da Conta** → **Conectores**.
2. Clique em **"+ Conector personalizado"**.
3. Preencha:
   - **Nome**: `Kalodata TikTok Shop Analytics`
   - **Tipo**: `Remoto`
   - **URL**: `https://kalodata-mcp.onrender.com/mcp`
   - **Transporte**: `Streamable HTTP`
   - **Autenticação**: `Nenhuma`
4. Salve. O Perplexity descobrirá automaticamente as 8 ferramentas.

> **Por que "Nenhuma" autenticação?** A chave da Kalodata fica no servidor (variável de ambiente), nunca exposta ao Perplexity.

---

## ✅ Checklist de Deploy Manual (Tarefas Fora do Agente)

Estas etapas dependem de contas externas e devem ser executadas por você manualmente:

- [ ] **1. GitHub** — Criar repositório `kalodata-mcp` no GitHub (pode ser privado).
- [ ] **2. Git Push** — Rodar `git remote add origin <URL>` e `git push -u origin master`.
- [ ] **3. Render** — Criar conta em [render.com](https://render.com) se ainda não tiver.
- [ ] **4. Blueprint** — No Render: **New +** → **Blueprint** → conectar repositório → detecta `render.yaml` automaticamente.
- [ ] **5. Variáveis secretas** — No painel do Render, preencher `KALODATA_SECRET_KEY` e `KALODATA_BASE_URL` manualmente (nunca commite esses valores).
- [ ] **6. Aguardar deploy** — O Render executa `pip install -r requirements.txt` e `python server.py`. Aguardar status "Live".
- [ ] **7. Testar endpoint público** — Copiar a URL gerada (ex: `https://kalodata-mcp.onrender.com`) e testar o endpoint `/mcp` com curl.
- [ ] **8. Perplexity** — Ir em **Configurações → Conectores → + Conector personalizado → Remoto** → colar `https://<url>/mcp` → Streamable HTTP → Autenticação: Nenhuma.

---

## 🔒 Aviso de Segurança

- **NUNCA comite o arquivo `.env`** com chave real. O `.gitignore` já o ignora.
- **NUNCA adicione a chave dentro do `render.yaml`** — as variáveis `sync: false` são inseridas manualmente no dashboard do Render.
- A chave da Kalodata vive apenas na variável de ambiente do servidor, nunca exposta ao cliente MCP.
