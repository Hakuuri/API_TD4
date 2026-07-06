"""Module partage (lot C), importable tel quel par api_rest et api_graphql.

Expose :
- creer_token(...) : genere un JWT au format du contrat d'interface
  {"sub": ..., "role": ..., "exp": ...}
- verifier_acces(role_requis=None) : dependance FastAPI qui verifie le token
  et, si demande, le role requis pour la route.
"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, REFRESH_TOKEN_EXPIRE_DAYS, SECRET_KEY

_bearer_scheme = HTTPBearer()


def creer_token(sub: str, role: str, type_token: str = "access") -> str:
    """Cree un JWT signe. type_token vaut "access" ou "refresh"."""
    if type_token == "refresh":
        expiration = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    else:
        expiration = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {"sub": sub, "role": role, "exp": expiration}
    if type_token == "refresh":
        payload["type"] = "refresh"

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decoder_token(token: str) -> dict:
    """Decode et verifie la signature/expiration d'un token. Leve HTTPException si invalide."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expire")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")


def verifier_acces(role_requis: str | None = None):
    """Dependance FastAPI : verifie le token porteur et, si role_requis est fourni,
    que le role du payload correspond. A utiliser ainsi :

        @app.post("/medias")
        def creer_media(payload: dict = Depends(verifier_acces(role_requis="bibliothecaire"))):
            ...
    """

    def dependency(credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme)) -> dict:
        payload = decoder_token(credentials.credentials)

        if payload.get("type") == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Un refresh_token ne peut pas etre utilise comme access_token",
            )

        if role_requis is not None and payload.get("role") != role_requis:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role_requis}' requis pour cette action",
            )

        return payload

    return dependency
