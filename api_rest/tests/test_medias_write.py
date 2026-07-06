import pytest
from fastapi.testclient import TestClient

from api_rest.app import _reset_store, app
from auth_securite.verification import creer_token

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    _reset_store()
    yield
    _reset_store()


def _token(role: str) -> str:
    return creer_token(sub="test-user", role=role)


def _headers(role: str) -> dict:
    return {"Authorization": f"Bearer {_token(role)}"}


MEDIA_VALIDE = {
    "titre": "Dune",
    "type": "livre",
    "auteur": "Frank Herbert",
    "annee": 1965,
    "disponible": True,
}


# --- POST /medias ---

def test_post_medias_sans_token_renvoie_401_ou_403():
    response = client.post("/medias", json=MEDIA_VALIDE)
    assert response.status_code in (401, 403)


def test_post_medias_role_usager_renvoie_403():
    response = client.post("/medias", json=MEDIA_VALIDE, headers=_headers("usager"))
    assert response.status_code == 403


def test_post_medias_role_bibliothecaire_cree_le_media():
    response = client.post("/medias", json=MEDIA_VALIDE, headers=_headers("bibliothecaire"))
    assert response.status_code == 201
    body = response.json()
    assert body["titre"] == "Dune"
    assert body["id"] == 1


def test_post_medias_payload_invalide_renvoie_400():
    payload_invalide = {"titre": "Dune"}  # champs obligatoires manquants
    response = client.post("/medias", json=payload_invalide, headers=_headers("bibliothecaire"))
    assert response.status_code == 400


def test_post_medias_type_invalide_renvoie_400():
    payload_invalide = {**MEDIA_VALIDE, "type": "magazine"}
    response = client.post("/medias", json=payload_invalide, headers=_headers("bibliothecaire"))
    assert response.status_code == 400


# --- PUT /medias/{id} ---

def test_put_media_existant_modifie_les_champs_fournis():
    creation = client.post("/medias", json=MEDIA_VALIDE, headers=_headers("bibliothecaire"))
    media_id = creation.json()["id"]

    response = client.put(
        f"/medias/{media_id}",
        json={"disponible": False},
        headers=_headers("bibliothecaire"),
    )
    assert response.status_code == 200
    assert response.json()["disponible"] is False
    assert response.json()["titre"] == "Dune"  # inchange


def test_put_media_inexistant_renvoie_404():
    response = client.put(
        "/medias/999",
        json={"disponible": False},
        headers=_headers("bibliothecaire"),
    )
    assert response.status_code == 404


def test_put_media_role_usager_renvoie_403():
    creation = client.post("/medias", json=MEDIA_VALIDE, headers=_headers("bibliothecaire"))
    media_id = creation.json()["id"]

    response = client.put(
        f"/medias/{media_id}",
        json={"disponible": False},
        headers=_headers("usager"),
    )
    assert response.status_code == 403


# --- DELETE /medias/{id} ---

def test_delete_media_existant_renvoie_204():
    creation = client.post("/medias", json=MEDIA_VALIDE, headers=_headers("bibliothecaire"))
    media_id = creation.json()["id"]

    response = client.delete(f"/medias/{media_id}", headers=_headers("bibliothecaire"))
    assert response.status_code == 204

    # Le media ne doit plus pouvoir etre modifie ensuite.
    response_put = client.put(
        f"/medias/{media_id}",
        json={"disponible": False},
        headers=_headers("bibliothecaire"),
    )
    assert response_put.status_code == 404


def test_delete_media_inexistant_renvoie_404():
    response = client.delete("/medias/999", headers=_headers("bibliothecaire"))
    assert response.status_code == 404


def test_delete_media_role_usager_renvoie_403():
    creation = client.post("/medias", json=MEDIA_VALIDE, headers=_headers("bibliothecaire"))
    media_id = creation.json()["id"]

    response = client.delete(f"/medias/{media_id}", headers=_headers("usager"))
    assert response.status_code == 403
