import sys
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import api_graphql.schema as schema_module
from api_graphql.app import app
from auth_securite.verification import verifier_acces

client = TestClient(app)
GRAPHQL_URL = "/graphql"


def bypass_auth():
    pass


@pytest.fixture(autouse=True)
def reset_state():
    """Réinitialise les données entre chaque test pour garantir l'indépendance."""
    schema_module._emprunts.clear()
    for m in schema_module._medias:
        m["disponible"] = True
    schema_module._medias[2]["disponible"] = False  # Zelda indisponible par défaut
    app.dependency_overrides[verifier_acces] = bypass_auth
    yield
    app.dependency_overrides.clear()


# --- Query medias ---

def test_query_medias_retourne_tous_les_medias():
    query = "{ medias { id titre disponible } }"
    response = client.post(GRAPHQL_URL, json={"query": query})
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    assert len(data["data"]["medias"]) == 3


def test_query_medias_filtre_disponible_true():
    query = "{ medias(disponible: true) { id titre disponible } }"
    response = client.post(GRAPHQL_URL, json={"query": query})
    assert response.status_code == 200
    medias = response.json()["data"]["medias"]
    assert len(medias) == 2
    assert all(m["disponible"] for m in medias)


def test_query_medias_filtre_titre_partiel():
    query = '{ medias(titre: "Dune") { id titre } }'
    response = client.post(GRAPHQL_URL, json={"query": query})
    assert response.status_code == 200
    medias = response.json()["data"]["medias"]
    assert len(medias) == 1
    assert medias[0]["titre"] == "Dune"


def test_query_medias_filtre_auteur():
    query = '{ medias(auteur: "Nolan") { id titre auteur } }'
    response = client.post(GRAPHQL_URL, json={"query": query})
    assert response.status_code == 200
    medias = response.json()["data"]["medias"]
    assert len(medias) == 1
    assert "Nolan" in medias[0]["auteur"]


def test_query_medias_filtres_combines():
    query = '{ medias(disponible: true, auteur: "Herbert") { id titre } }'
    response = client.post(GRAPHQL_URL, json={"query": query})
    assert response.status_code == 200
    medias = response.json()["data"]["medias"]
    assert len(medias) == 1
    assert medias[0]["titre"] == "Dune"


# --- Query statistiques ---

def test_query_statistiques_vide_sans_emprunts():
    query = "{ statistiques { mediaId titre nombreEmprunts } }"
    response = client.post(GRAPHQL_URL, json={"query": query})
    assert response.status_code == 200
    assert response.json()["data"]["statistiques"] == []


def test_query_statistiques_retourne_top3():
    # Emprunter le média 1 deux fois et le média 2 une fois
    schema_module._emprunts.extend([
        {"id": 1, "media_id": 1, "retourne": True},
        {"id": 2, "media_id": 1, "retourne": True},
        {"id": 3, "media_id": 2, "retourne": False},
    ])
    query = "{ statistiques { mediaId titre nombreEmprunts } }"
    response = client.post(GRAPHQL_URL, json={"query": query})
    assert response.status_code == 200
    stats = response.json()["data"]["statistiques"]
    assert len(stats) == 2
    assert stats[0]["nombreEmprunts"] >= stats[1]["nombreEmprunts"]
    assert stats[0]["mediaId"] == 1


# --- Mutation demanderEmprunt ---

def test_mutation_demander_emprunt_succes():
    mutation = "mutation { demanderEmprunt(mediaId: 1) { id mediaId retourne } }"
    response = client.post(GRAPHQL_URL, json={"query": mutation})
    assert response.status_code == 200
    data = response.json()
    assert "errors" not in data
    emprunt = data["data"]["demanderEmprunt"]
    assert emprunt["mediaId"] == 1
    assert emprunt["retourne"] is False
    assert len(schema_module._emprunts) == 1


def test_mutation_demander_emprunt_media_deja_emprunte():
    schema_module._medias[0]["disponible"] = False
    mutation = "mutation { demanderEmprunt(mediaId: 1) { id } }"
    response = client.post(GRAPHQL_URL, json={"query": mutation})
    data = response.json()
    assert "errors" in data
    assert "déjà emprunté" in data["errors"][0]["message"]


def test_mutation_demander_emprunt_media_inexistant():
    mutation = "mutation { demanderEmprunt(mediaId: 999) { id } }"
    response = client.post(GRAPHQL_URL, json={"query": mutation})
    data = response.json()
    assert "errors" in data
    assert "introuvable" in data["errors"][0]["message"]


# --- Auth ---

def test_refus_401_sans_token():
    app.dependency_overrides.clear()

    def verifier_non_authentifie():
        raise HTTPException(status_code=401, detail="Non authentifié")

    app.dependency_overrides[verifier_acces] = verifier_non_authentifie
    query = "{ medias { id } }"
    response = client.post(GRAPHQL_URL, json={"query": query})
    assert response.status_code == 401
