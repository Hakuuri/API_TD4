"""Lot C - Securite : authentification, roles.

Framework : FastAPI, choisi pour l'injection de dependances (Depends) qui
permet de brancher verifier_acces() directement sur les routes des lots A et B
sans dupliquer de logique de controle d'acces.
"""

from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from pydantic import BaseModel

from auth_securite.verification import creer_token, decoder_token

app = FastAPI(title="Mediatheque augmentee - Auth & Securite")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Stockage en memoire pour ce TD (pas de base de donnees requise par le cahier des charges).
utilisateurs_db: dict[str, dict] = {}


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.errors()})


class Inscription(BaseModel):
    username: str
    password: str
    role: Literal["usager", "bibliothecaire"]


class Identifiants(BaseModel):
    username: str
    password: str


class RefreshDemande(BaseModel):
    refresh_token: str


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(inscription: Inscription):
    if inscription.username in utilisateurs_db:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ce compte existe deja")

    utilisateurs_db[inscription.username] = {
        "username": inscription.username,
        "password_hash": pwd_context.hash(inscription.password),
        "role": inscription.role,
    }
    return {"username": inscription.username, "role": inscription.role}


@app.post("/auth/login", response_model=Tokens)
def login(identifiants: Identifiants):
    utilisateur = utilisateurs_db.get(identifiants.username)
    if utilisateur is None or not pwd_context.verify(identifiants.password, utilisateur["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")

    access_token = creer_token(sub=utilisateur["username"], role=utilisateur["role"], type_token="access")
    refresh_token = creer_token(sub=utilisateur["username"], role=utilisateur["role"], type_token="refresh")
    return Tokens(access_token=access_token, refresh_token=refresh_token)


@app.post("/auth/refresh", response_model=Tokens)
def refresh(demande: RefreshDemande):
    payload = decoder_token(demande.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="refresh_token attendu")

    utilisateur = utilisateurs_db.get(payload["sub"])
    if utilisateur is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inconnu")

    nouveau_access_token = creer_token(sub=utilisateur["username"], role=utilisateur["role"], type_token="access")
    return Tokens(access_token=nouveau_access_token, refresh_token=demande.refresh_token)
