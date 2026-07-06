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


def _headers(role: str) -> dict:
    token = creer_token(sub="test-user", role=role)
    return {"Authorization": f"Bearer {token}"}


def _creer_media(disponible: bool = True) -> int:
    reponse = client.post(
        "/medias",
        json={
            "titre": "Dune",
            "type": "livre",
            "auteur": "Frank Herbert",
            "annee": 1965,
            "disponible": disponible,
        },
        headers=_headers("bibliothecaire"),
    )
    return reponse.json()["id"]


# --- GET /medias ---

def test_get_medias_sans_token_renvoie_401_ou_403():
    response = client.get("/medias")
    assert response.status_code in (401, 403)


def test_get_medias_accessible_a_tout_role_authentifie():
    _creer_media()
    response = client.get("/medias", headers=_headers("usager"))
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_medias_filtre_par_type_et_disponibilite():
    _creer_media(disponible=True)
    client.post(
        "/medias",
        json={"titre": "Inception", "type": "dvd", "auteur": "Nolan", "annee": 2010, "disponible": False},
        headers=_headers("bibliothecaire"),
    )

    response = client.get("/medias", params={"type": "dvd"}, headers=_headers("usager"))
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["titre"] == "Inception"

    response = client.get("/medias", params={"disponible": True}, headers=_headers("usager"))
    assert [m["titre"] for m in response.json()] == ["Dune"]


# --- GET /medias/{id} ---

def test_get_media_existant():
    media_id = _creer_media()
    response = client.get(f"/medias/{media_id}", headers=_headers("usager"))
    assert response.status_code == 200
    assert response.json()["titre"] == "Dune"


def test_get_media_inexistant_renvoie_404():
    response = client.get("/medias/999", headers=_headers("usager"))
    assert response.status_code == 404


# --- POST /medias/{id}/emprunt ---

def test_emprunt_media_disponible():
    media_id = _creer_media(disponible=True)
    response = client.post(f"/medias/{media_id}/emprunt", headers=_headers("usager"))
    assert response.status_code == 201
    assert response.json()["media_id"] == media_id

    fiche_media = client.get(f"/medias/{media_id}", headers=_headers("usager")).json()
    assert fiche_media["disponible"] is False


def test_emprunt_media_deja_emprunte_renvoie_409():
    media_id = _creer_media(disponible=True)
    client.post(f"/medias/{media_id}/emprunt", headers=_headers("usager"))

    response = client.post(f"/medias/{media_id}/emprunt", headers=_headers("usager"))
    assert response.status_code == 409


def test_emprunt_media_inexistant_renvoie_404():
    response = client.post("/medias/999/emprunt", headers=_headers("usager"))
    assert response.status_code == 404


def test_emprunt_sans_token_renvoie_401_ou_403():
    media_id = _creer_media()
    response = client.post(f"/medias/{media_id}/emprunt")
    assert response.status_code in (401, 403)


# --- POST /emprunts/{id}/retour ---

def test_retour_emprunt_remet_le_media_disponible():
    media_id = _creer_media(disponible=True)
    emprunt = client.post(f"/medias/{media_id}/emprunt", headers=_headers("usager")).json()

    response = client.post(f"/emprunts/{emprunt['id']}/retour", headers=_headers("usager"))
    assert response.status_code == 200
    assert response.json()["retourne"] is True

    fiche_media = client.get(f"/medias/{media_id}", headers=_headers("usager")).json()
    assert fiche_media["disponible"] is True


def test_retour_emprunt_inexistant_renvoie_404():
    response = client.post("/emprunts/999/retour", headers=_headers("usager"))
    assert response.status_code == 404
