import logging
import os
import time
import webbrowser
from urllib.parse import urlencode

import httpx

logger = logging.getLogger(__name__)


ML_AUTH_URL = "https://auth.mercadolivre.com.br/authorization"
ML_TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
ML_API_BASE = "https://api.mercadolibre.com"

ML_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}


class MercadoLivreAPIClient:
    def __init__(self, app_id: str | None = None, client_secret: str | None = None):
        self.app_id = app_id or os.getenv("ML_APP_ID", "")
        self.client_secret = client_secret or os.getenv("ML_CLIENT_SECRET", "")
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.token_expires_at: float = 0.0

    def is_configured(self) -> bool:
        return bool(self.app_id and self.client_secret)

    def get_auth_url(self, redirect_uri: str = "https://localhost:3000") -> str:
        params = {
            "response_type": "code",
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
        }
        return f"{ML_AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str, redirect_uri: str = "https://localhost:3000") -> bool:
        try:
            resp = httpx.post(
                ML_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.app_id,
                    "client_secret": self.client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
                headers=ML_HEADERS,
                timeout=15,
            )
            if resp.status_code != 200:
                logger.error("ML API: erro ao trocar code por token: %s", resp.text)
                return False
            data = resp.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token")
            self.token_expires_at = time.time() + data.get("expires_in", 21600)
            logger.info("ML API: token obtido com sucesso, expira em %ds", data.get("expires_in", 21600))
            return True
        except Exception as e:
            logger.error("ML API: erro ao trocar code: %s", e)
            return False

    def refresh_access_token(self) -> bool:
        if not self.refresh_token:
            logger.warning("ML API: sem refresh_token para renovar")
            return False
        try:
            resp = httpx.post(
                ML_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "client_id": self.app_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                },
                headers=ML_HEADERS,
                timeout=15,
            )
            if resp.status_code != 200:
                logger.error("ML API: erro ao renovar token: %s", resp.text)
                return False
            data = resp.json()
            self.access_token = data.get("access_token")
            self.refresh_token = data.get("refresh_token", self.refresh_token)
            self.token_expires_at = time.time() + data.get("expires_in", 21600)
            logger.info("ML API: token renovado com sucesso")
            return True
        except Exception as e:
            logger.error("ML API: erro ao renovar token: %s", e)
            return False

    def _ensure_token(self) -> str | None:
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token

        if self.refresh_token:
            if self.refresh_access_token():
                return self.access_token

        token_env = os.getenv("ML_ACCESS_TOKEN")
        if token_env:
            self.access_token = token_env
            self.token_expires_at = time.time() + 21600
            logger.info("ML API: usando token do env ML_ACCESS_TOKEN")
            return self.access_token

        return None

    def search(self, query: str, limit: int = 20) -> list[dict] | None:
        token = self._ensure_token()
        if not token:
            logger.warning("ML API: sem token disponivel para busca")
            return None

        headers = {**ML_HEADERS, "Authorization": f"Bearer {token}"}

        try:
            resp = httpx.get(
                f"{ML_API_BASE}/sites/MLB/search",
                params={"q": query, "limit": limit},
                headers=headers,
                timeout=15,
            )
            if resp.status_code == 401:
                logger.warning("ML API: token expirado, tentando renovar")
                if self.refresh_access_token():
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    resp = httpx.get(
                        f"{ML_API_BASE}/sites/MLB/search",
                        params={"q": query, "limit": limit},
                        headers=headers,
                        timeout=15,
                    )

            if resp.status_code == 403:
                logger.warning("ML API: acesso proibido mesmo com token (Akamai)")
                return None

            resp.raise_for_status()
            data = resp.json()

            results = data.get("results", [])
            if not results:
                logger.info("ML API: 0 resultados para '%s'", query)
                return []

            items = []
            for item in results:
                title = item.get("title", "").strip()
                price = item.get("price")
                permalink = item.get("permalink", "")
                seller = item.get("seller", {})
                seller_name = seller.get("nickname") if seller else None

                if not title or price is None:
                    continue

                items.append({
                    "title": title,
                    "price_text": f"{float(price):.2f}",
                    "seller_name": seller_name,
                    "listing_url": permalink,
                })

            logger.info("ML API: %d resultados para '%s'", len(items), query)
            return items

        except httpx.HTTPStatusError as e:
            logger.warning("ML API: erro HTTP %d na busca '%s': %s", e.response.status_code, query, e)
            return None
        except Exception as e:
            logger.error("ML API: erro na busca '%s': %s", query, e)
            return None

    def search_with_fallback(self, query: str, limit: int = 20) -> list[dict] | None:
        """Tenta busca autenticada. Se não tiver token configurado, retorna None."""
        if not self.is_configured():
            logger.info("ML API: credenciais nao configuradas (ML_APP_ID/ML_CLIENT_SECRET)")
            return None
        return self.search(query, limit)


def print_auth_instructions():
    inst = """
=== MERCADO LIVRE API — PRIMEIRA CONFIGURACAO ===

1. Acesse https://developers.mercadolivre.com.br
2. Clique em "Criar aplicacao"
3. Preencha nome, descricao, e em "Redirect URI" coloque: https://localhost:3000
4. Apos criar, copie o APP_ID e CLIENT_SECRET
5. Adicione no .env:
     ML_APP_ID=seu_app_id
     ML_CLIENT_SECRET=seu_client_secret

6. Para gerar o primeiro access token:
   a) Acesse a URL abaixo no navegador (enquanto logado no ML):
"""
    print(inst)


def print_auth_url(app_id: str):
    url = f"{ML_AUTH_URL}?{urlencode({'response_type': 'code', 'client_id': app_id, 'redirect_uri': 'https://localhost:3000'})}"
    print(f"   {url}")
    print("""
   b) Autorize o app
   c) A URL sera redirecionada para algo como:
      https://localhost:3000/?code=TG-123456...
   d) Copie o codigo (depois de ?code=) e use:

   from scraper.mercadolivre_api import MercadoLivreAPIClient
   client = MercadoLivreAPIClient()
   client.exchange_code("TG-123456...")
   print("Access token:", client.access_token)
   print("Refresh token:", client.refresh_token)

   e) Coloque o access_token no .env:
      ML_ACCESS_TOKEN=seu_access_token

Pronto! O cliente vai usar o token e renovar automaticamente com o refresh_token.
""")
