import sys
from pathlib import Path

from fastapi import HTTPException
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[1]
API_REST_DIR = ROOT_DIR / "api_rest"

for path in (ROOT_DIR, API_REST_DIR):
	if str(path) not in sys.path:
		sys.path.insert(0, str(path))

from main import app
from auth_securite.verification import verifier_acces


client = TestClient(app)


def teardown_function():
	app.dependency_overrides.clear()


def test_refus_401_sur_liste_medias():
	def verifier_refus_401():
		raise HTTPException(status_code=401, detail="Non authentifié")

	app.dependency_overrides[verifier_acces] = verifier_refus_401

	response = client.get("/medias")

	assert response.status_code == 401
	assert response.json()["detail"] == "Non authentifié"


def test_refus_403_sur_emprunt():
	def verifier_refus_403():
		raise HTTPException(status_code=403, detail="Accès interdit")

	app.dependency_overrides[verifier_acces] = verifier_refus_403

	response = client.post("/medias/1/emprunt")

	assert response.status_code == 403
	assert response.json()["detail"] == "Accès interdit"