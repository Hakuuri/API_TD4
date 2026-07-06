import pytest
from fastapi.testclient import TestClient

from auth_securite.app import app, utilisateurs_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_db():
    utilisateurs_db.clear()
    yield
    utilisateurs_db.clear()


def test_register_cree_un_compte():
    response = client.post(
        "/auth/register",
        json={"username": "alice", "password": "motdepasse123", "role": "usager"},
    )
    assert response.status_code == 201
    assert response.json() == {"username": "alice", "role": "usager"}


def test_register_ne_stocke_jamais_le_mot_de_passe_en_clair():
    client.post(
        "/auth/register",
        json={"username": "bob", "password": "motdepasse123", "role": "bibliothecaire"},
    )
    assert utilisateurs_db["bob"]["password_hash"] != "motdepasse123"


def test_register_compte_existant_renvoie_409():
    client.post("/auth/register", json={"username": "alice", "password": "x", "role": "usager"})
    response = client.post("/auth/register", json={"username": "alice", "password": "y", "role": "usager"})
    assert response.status_code == 409


def test_register_role_invalide_renvoie_400():
    response = client.post(
        "/auth/register",
        json={"username": "carole", "password": "x", "role": "administrateur"},
    )
    assert response.status_code == 400


def test_login_avec_bons_identifiants():
    client.post("/auth/register", json={"username": "alice", "password": "motdepasse123", "role": "usager"})
    response = client.post("/auth/login", json={"username": "alice", "password": "motdepasse123"})
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


def test_login_avec_mauvais_mot_de_passe_renvoie_401():
    client.post("/auth/register", json={"username": "alice", "password": "motdepasse123", "role": "usager"})
    response = client.post("/auth/login", json={"username": "alice", "password": "faux"})
    assert response.status_code == 401


def test_login_utilisateur_inconnu_renvoie_401():
    response = client.post("/auth/login", json={"username": "inconnu", "password": "x"})
    assert response.status_code == 401


def test_refresh_renvoie_un_nouvel_access_token():
    client.post("/auth/register", json={"username": "alice", "password": "motdepasse123", "role": "usager"})
    login_resp = client.post("/auth/login", json={"username": "alice", "password": "motdepasse123"})
    refresh_token = login_resp.json()["refresh_token"]

    response = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_refresh_avec_access_token_renvoie_401():
    client.post("/auth/register", json={"username": "alice", "password": "motdepasse123", "role": "usager"})
    login_resp = client.post("/auth/login", json={"username": "alice", "password": "motdepasse123"})
    access_token = login_resp.json()["access_token"]

    response = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert response.status_code == 401
