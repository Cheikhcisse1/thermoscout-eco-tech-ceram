"""Protection d'accès pour le déploiement en ligne (mot de passe, limite de requêtes, en-têtes).

- APP_PASSWORD : si défini, tout l'accès est protégé par mot de passe (authentification HTTP Basic, nom d'utilisateur libre).
- REQUIRE_AUTH=1 (positionné dans le Dockerfile) : le serveur REFUSE de démarrer sans APP_PASSWORD.
- RATE_LIMIT_PER_HOUR : nombre max. de requêtes « coûteuses » (IA, import) par IP et par heure. Actif en ligne
  (REQUIRE_AUTH=1) ou si la variable est définie ; désactivé en usage local.
- PUBLIC_MODE=1 : démo ouverte à tous, sans mot de passe (la limite par IP reste active).
- /healthz reste public (sonde de l'hébergeur) et ne révèle rien.
"""
import base64
import binascii
import os
import secrets
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse, Response


def _authorized(request: Request, password: str) -> bool:
    header = request.headers.get("authorization", "")
    if not header.lower().startswith("basic "):
        return False
    try:
        given = base64.b64decode(header[6:]).decode("utf-8").partition(":")[2]
    except (binascii.Error, UnicodeDecodeError):
        return False
    return secrets.compare_digest(given.encode(), password.encode())


def install(app, limited_prefixes: tuple[str, ...]):
    password = os.getenv("APP_PASSWORD", "")
    public = os.getenv("PUBLIC_MODE") == "1"
    if os.getenv("REQUIRE_AUTH") == "1" and not password and not public:
        raise RuntimeError("APP_PASSWORD est obligatoire en déploiement (REQUIRE_AUTH=1).")
    limit_on = os.getenv("REQUIRE_AUTH") == "1" or bool(os.getenv("RATE_LIMIT_PER_HOUR"))
    limit = int(os.getenv("RATE_LIMIT_PER_HOUR", "30"))
    hits: dict[str, deque] = defaultdict(deque)

    @app.middleware("http")
    async def guard(request: Request, call_next):
        path = request.url.path
        if path != "/healthz":
            if password and not _authorized(request, password):
                return Response("Authentification requise", 401,
                                headers={"WWW-Authenticate": 'Basic realm="Acces prive", charset="UTF-8"'})
            if limit_on and request.method == "POST" and path.startswith(limited_prefixes):
                fwd = request.headers.get("x-forwarded-for", "")
                ip = fwd.split(",")[-1].strip() or (request.client.host if request.client else "?")
                now, q = time.time(), hits[ip]
                while q and now - q[0] > 3600:
                    q.popleft()
                if len(q) >= limit:
                    return JSONResponse({"detail": f"Trop de requêtes : maximum {limit} par heure. Réessaie plus tard."}, 429)
                q.append(now)
                if len(hits) > 5000:  # évite une croissance sans fin de la mémoire
                    for k in [k for k, v in hits.items() if not v]:
                        del hits[k]
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        return response

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}
