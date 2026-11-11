import os
import json
import httpx
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

KALODATA_SECRET_KEY = os.getenv("KALODATA_SECRET_KEY")
KALODATA_BASE_URL = os.getenv("KALODATA_BASE_URL", "https://staging.kalodata.com").rstrip("/")
PORT = int(os.getenv("PORT", "8000"))
HOST = os.getenv("HOST", "0.0.0.0")
# Token opcional que vira parte da rota (/mcp/<token>). Protege a URL pública,
# já que conectores remotos sem autenticação podem ser usados por quem tiver a URL.
MCP_PATH_TOKEN = os.getenv("MCP_PATH_TOKEN", "").strip().strip("/")
MCP_PATH = f"/mcp/{MCP_PATH_TOKEN}" if MCP_PATH_TOKEN else "/mcp"

if not KALODATA_SECRET_KEY:
    raise ValueError(
        "A variável de ambiente KALODATA_SECRET_KEY não foi configurada! "
        "Defina KALODATA_SECRET_KEY no seu arquivo .env ou no painel de hospedagem."
    )

async def call_kalodata(path: str, payload: dict) -> dict:
    """
    Função assíncrona genérica para realizar requisições POST à Kalodata Open API.
    Monta os cabeçalhos de autenticação e trata erros de conexão e status HTTP.
    """
    url = f"{KALODATA_BASE_URL}{path}"
    headers = {
        "secret-key": KALODATA_SECRET_KEY,
        "content-type": "application/json;charset=utf-8"
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code >= 400:
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": f"Erro na requisição Kalodata (HTTP {response.status_code}): {response.text}"
                }
            return response.json()
        except httpx.TimeoutException:
            return {
                "error": True,
                "status_code": 408,
                "message": "Tempo limite esgotado (timeout de 15s) ao conectar à Kalodata API."
            }
        except httpx.RequestError as exc:
            return {
                "error": True,
                "status_code": 500,
                "message": f"Erro de comunicação com o servidor Kalodata: {str(exc)}"
            }

def _clean_payload(base_params: dict, extra_params: dict) -> dict:
    """Filtra parâmetros opcionais nulos (None) do payload final."""
    payload = {**base_params}
    for k, v in extra_params.items():
        if v is not None:
            payload[k] = v
    return payload

# Instância do Servidor MCP — HOST e PORT lidos de variáveis de ambiente
mcp = FastMCP("kalodata", host=HOST, port=PORT, streamable_http_path=MCP_PATH)

@mcp.tool()
async def category_rank(
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day",
    category_id: Optional[str] = None,
    category_level: Optional[int] = None,
    revenue_range: Optional[Dict[str, Any]] = None,
    sort_field: Optional[Dict[str, str]] = None,
    page_number: int = 1
) -> str:
    """
    Retorna o ranking de categorias de produtos do TikTok Shop por receita (faturamento).
    Utilize esta ferramenta para identificar quais nichos/categorias estão gerando maior volume de vendas.
    """
    if sort_field is None:
        sort_field = {"field": "revenue", "type": "DESC"}
        
    base = {
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range,
        "sort_field": sort_field,
        "page_number": page_number
    }
    extra = {
        "category_id": category_id,
        "category_level": category_level,
        "revenue_range": revenue_range
    }
    payload = _clean_payload(base, extra)
    result = await call_kalodata("/openapi/v1/category/rank", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def category_detail(
    category_id: str,
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day"
) -> str:
    """
    Retorna os detalhes completos de uma categoria específica no TikTok Shop a partir do ID da categoria.
    Fornece métricas aprofundadas sobre vendas, taxa de crescimento e comportamento da categoria.
    """
    payload = {
        "category_id": category_id,
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range
    }
    result = await call_kalodata("/openapi/v1/category/detail", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def product_rank(
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day",
    category_id: Optional[str] = None,
    shop_id: Optional[str] = None,
    creator_id: Optional[str] = None,
    video_id: Optional[str] = None,
    revenue_range: Optional[Dict[str, Any]] = None,
    is_affiliate: Optional[str] = None,
    commission_rate: Optional[Dict[str, Any]] = None,
    unit_price_range: Optional[Dict[str, Any]] = None,
    sort_field: Optional[Dict[str, str]] = None,
    page_number: int = 1
) -> str:
    """
    Retorna o ranking de produtos mais vendidos no TikTok Shop.
    Permite filtrar por categoria, loja, criador, taxa de comissão e preço. Útil para minerar produtos campeões de vendas (winning products).
    """
    if sort_field is None:
        sort_field = {"field": "revenue", "type": "DESC"}
        
    base = {
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range,
        "sort_field": sort_field,
        "page_number": page_number
    }
    extra = {
        "category_id": category_id,
        "shop_id": shop_id,
        "creator_id": creator_id,
        "video_id": video_id,
        "revenue_range": revenue_range,
        "is_affiliate": is_affiliate,
        "commission_rate": commission_rate,
        "unit_price_range": unit_price_range
    }
    payload = _clean_payload(base, extra)
    result = await call_kalodata("/openapi/v1/product/rank", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def product_detail(
    product_id: str,
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day"
) -> str:
    """
    Retorna detalhes minuciosos sobre um produto específico no TikTok Shop através do seu ID de produto.
    Exibe dados de vendas, comissão de afiliados, lojas associadas e vídeos promocionais.
    """
    payload = {
        "product_id": product_id,
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range
    }
    result = await call_kalodata("/openapi/v1/product/detail", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def creator_rank(
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day",
    category_id: Optional[str] = None,
    shop_id: Optional[str] = None,
    revenue_range: Optional[Dict[str, Any]] = None,
    creator_type: Optional[str] = None,
    followers_range: Optional[str] = None,
    engagement_rate: Optional[str] = None,
    sort_field: Optional[Dict[str, str]] = None,
    page_number: int = 1
) -> str:
    """
    Retorna o ranking de criadores/influenciadores no TikTok Shop ordenados por faturamento gerado.
    Permite filtrar por tipo de criador, quantidade de seguidores e taxa de engajamento para encontrar parceiros ideais.
    """
    if sort_field is None:
        sort_field = {"field": "revenue", "type": "DESC"}

    base = {
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range,
        "sort_field": sort_field,
        "page_number": page_number
    }
    extra = {
        "category_id": category_id,
        "shop_id": shop_id,
        "revenue_range": revenue_range,
        "creator_type": creator_type,
        "followers_range": followers_range,
        "engagement_rate": engagement_rate
    }
    payload = _clean_payload(base, extra)
    # Endpoint de criadores (caminho correto sem typo)
    result = await call_kalodata("/openapi/v1/creator/rank", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def creator_detail(
    creator_id: str,
    shop_id: Optional[str] = None,
    category_id: Optional[str] = None,
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day"
) -> str:
    """
    Retorna estatísticas detalhadas de um criador de conteúdo específico no TikTok Shop.
    Analisa métricas de vendas acumuladas, engajamento dos vídeos e histórico de performance.
    """
    base = {
        "creator_id": creator_id,
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range
    }
    extra = {
        "shop_id": shop_id,
        "category_id": category_id
    }
    payload = _clean_payload(base, extra)
    # Endpoint de criadores (caminho correto sem typo)
    result = await call_kalodata("/openapi/v1/creator/detail", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def video_rank(
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day",
    category_id: Optional[str] = None,
    shop_id: Optional[str] = None,
    creator_id: Optional[str] = None,
    product_id: Optional[str] = None,
    revenue_range: Optional[Dict[str, Any]] = None,
    followers_range: Optional[str] = None,
    ads_roas: Optional[Dict[str, Any]] = None,
    sort_field: Optional[Dict[str, str]] = None,
    page_number: int = 1
) -> str:
    """
    Retorna o ranking de vídeos virais que mais venderam no TikTok Shop.
    Essencial para pesquisas de criativos de alta conversão, análise de ganchos (hooks) e ROAS de anúncios.
    """
    if sort_field is None:
        sort_field = {"field": "revenue", "type": "DESC"}

    base = {
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range,
        "sort_field": sort_field,
        "page_number": page_number
    }
    extra = {
        "category_id": category_id,
        "shop_id": shop_id,
        "creator_id": creator_id,
        "product_id": product_id,
        "revenue_range": revenue_range,
        "followers_range": followers_range,
        "ads_roas": ads_roas
    }
    payload = _clean_payload(base, extra)
    result = await call_kalodata("/openapi/v1/video/rank", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def video_detail(
    video_id: str,
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day"
) -> str:
    """
    Retorna o detalhamento completo e métricas de desempenho de um vídeo específico no TikTok Shop.
    Fornece dados sobre receita gerada, visualizações, curtidas e produtos vinculados ao vídeo.
    """
    payload = {
        "video_id": video_id,
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range
    }
    result = await call_kalodata("/openapi/v1/video/detail", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def shop_rank(
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day",
    category_id: Optional[str] = None,
    revenue_range: Optional[Dict[str, Any]] = None,
    shop_type: Optional[str] = None,
    sort_field: Optional[Dict[str, str]] = None,
    page_number: int = 1
) -> str:
    """
    Retorna o ranking das lojas (shops) com maior faturamento no TikTok Shop.
    Permite filtrar por categoria de produto, faixa de receita e tipo de loja.
    """
    if sort_field is None:
        sort_field = {"field": "revenue", "type": "DESC"}

    base = {
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range,
        "sort_field": sort_field,
        "page_number": page_number
    }
    extra = {
        "category_id": category_id,
        "revenue_range": revenue_range,
        "shop_type": shop_type
    }
    payload = _clean_payload(base, extra)
    result = await call_kalodata("/openapi/v1/shop/rank", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def shop_detail(
    shop_id: str,
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day"
) -> str:
    """
    Retorna os detalhes e métricas de desempenho de uma loja específica no TikTok Shop através do seu ID de loja.
    Exibe dados de vendas totais, produtos mais vendidos, canal de afiliados e divisão de faturamento.
    """
    payload = {
        "shop_id": shop_id,
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range
    }
    result = await call_kalodata("/openapi/v1/shop/detail", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def livestream_rank(
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day",
    category_id: Optional[str] = None,
    shop_id: Optional[str] = None,
    creator_id: Optional[str] = None,
    revenue_range: Optional[Dict[str, Any]] = None,
    sort_field: Optional[Dict[str, str]] = None,
    page_number: int = 1
) -> str:
    """
    Retorna o ranking de transmissões ao vivo (livestreams) ordenadas por receita gerada no TikTok Shop.
    Útil para analisar quais lives geraram maior faturamento, pico de espectadores e produtos promovidos.
    """
    if sort_field is None:
        sort_field = {"field": "revenue", "type": "DESC"}

    base = {
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range,
        "sort_field": sort_field,
        "page_number": page_number
    }
    extra = {
        "category_id": category_id,
        "shop_id": shop_id,
        "creator_id": creator_id,
        "revenue_range": revenue_range
    }
    payload = _clean_payload(base, extra)
    result = await call_kalodata("/openapi/v1/livestream/rank", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

@mcp.tool()
async def livestream_detail(
    livestream_id: str,
    region: str = "US",
    language: str = "en-US",
    currency: str = "USD",
    date_range: str = "last7Day"
) -> str:
    """
    Retorna o detalhamento completo e estatísticas de uma transmissão ao vivo (livestream) específica no TikTok Shop.
    Fornece métricas de audiência, duração da live, faturamento total, GPM e produtos vendidos.
    """
    payload = {
        "livestream_id": livestream_id,
        "region": region,
        "language": language,
        "currency": currency,
        "date_range": date_range
    }
    result = await call_kalodata("/openapi/v1/livestream/detail", payload)
    return json.dumps(result, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    import sys

    # Modo stdio: o cliente (ex.: Claude Code) inicia e encerra o servidor sozinho.
    # Nada pode ser impresso no stdout neste modo, pois ele carrega o protocolo MCP.
    if "--stdio" in sys.argv or os.getenv("MCP_TRANSPORT") == "stdio":
        mcp.run(transport="stdio")
        sys.exit(0)

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    # Atualiza settings caso .env seja recarregado após a instanciação
    mcp.settings.host = host
    mcp.settings.port = port
    rota = "/mcp/<MCP_PATH_TOKEN>" if MCP_PATH_TOKEN else "/mcp"  # nunca imprime o token
    print(f"[kalodata-mcp] Servidor iniciando em http://{host}:{port}{rota}")
    print(f"[kalodata-mcp] Transporte: streamable-http | 12 ferramentas registradas")
    mcp.run(transport="streamable-http")


