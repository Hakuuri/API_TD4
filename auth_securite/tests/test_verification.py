import time

import jwt
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from common.config import ALGORITHM, SECRET_KEY
from auth_securite.verification import creer_token, decoder_token, verifier_acces


def test_creer_token_contient_les_champs_du_contrat():
    token = creer_token(sub="alice", role="usager")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

    assert payload["sub"] == "alice"
    assert payload["role"] == "usager"
    assert "exp" in payload


def test_decoder_token_valide():
    token = creer_token(sub="bob", role="bibliothecaire")
    payload = decoder_token(token)
    assert payload["sub"] == "bob"
    assert payload["role"] == "bibliothecaire"


def test_decoder_token_invalide_leve_401():
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        decoder_token("token.invalide.xyz")
    assert exc_info.value.status_code == 401


def test_decoder_token_expire_leve_401():
    from fastapi import HTTPException

    token = jwt.encode(
        {"sub": "carole", "role": "usager", "exp": int(time.time()) - 10},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    with pytest.raises(HTTPException) as exc_info:
        decoder_token(token)
    assert exc_info.value.status_code == 401


# --- Tests de verifier_acces() via une mini-app FastAPI, comme le feraient les lots A et B ---

_app_test = FastAPI()


@_app_test.get("/protege")
def route_protegee(payload: dict = Depends(verifier_acces())):
    return {"sub": payload["sub"]}


@_app_test.get("/reservee-bibliothecaire")
def route_reservee(payload: dict = Depends(verifier_acces(role_requis="bibliothecaire"))):
    return {"sub": payload["sub"]}


client = TestClient(_app_test)


def test_route_protegee_sans_token_renvoie_403_ou_401():
    response = client.get("/protege")
    assert response.status_code in (401, 403)


def test_route_protegee_avec_token_valide():
    token = creer_token(sub="dave", role="usager")
    response = client.get("/protege", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == {"sub": "dave"}


def test_route_reservee_refuse_role_usager():
    token = creer_token(sub="eve", role="usager")
    response = client.get("/reservee-bibliothecaire", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_route_reservee_accepte_role_bibliothecaire():
    token = creer_token(sub="frank", role="bibliothecaire")
    response = client.get("/reservee-bibliothecaire", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_refresh_token_refuse_comme_access_token():
    token = creer_token(sub="gina", role="usager", type_token="refresh")
    response = client.get("/protege", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
