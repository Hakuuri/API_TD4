import sys
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.append(str(ROOT_DIR))

from auth_securite.verification import verifier_acces


app = FastAPI()


MEDIA_INCONNU = "Média introuvable"


medias = [
	{
		"id": 1,
		"titre": "Dune",
		"type": "livre",
		"auteur": "Frank Herbert",
		"annee": 1965,
		"disponible": True,
	},
	{
		"id": 2,
		"titre": "Inception",
		"type": "dvd",
		"auteur": "Christopher Nolan",
		"annee": 2010,
		"disponible": True,
	},
	{
		"id": 3,
		"titre": "The Legend of Zelda: Breath of the Wild",
		"type": "jeu",
		"auteur": "Nintendo",
		"annee": 2017,
		"disponible": False,
	},
]

emprunts = []


def trouver_media(media_id: int):
	for media in medias:
		if media["id"] == media_id:
			return media
	return None


def trouver_emprunt(emprunt_id: int):
	for emprunt in emprunts:
		if emprunt["id"] == emprunt_id:
			return emprunt
	return None


@app.get("/medias", dependencies=[Depends(verifier_acces)])
def lire_medias(type: str | None = None, disponibilite: bool | None = Query(default=None)):
	resultat = medias

	if type is not None:
		resultat = [media for media in resultat if media["type"] == type]

	if disponibilite is not None:
		resultat = [media for media in resultat if media["disponible"] == disponibilite]

	return resultat


@app.get("/medias/{media_id}", dependencies=[Depends(verifier_acces)])
def lire_media(media_id: int):
	media = trouver_media(media_id)
	if media is not None:
		return media

	raise HTTPException(status_code=404, detail=MEDIA_INCONNU)


@app.post("/medias/{media_id}/emprunt", dependencies=[Depends(verifier_acces)])
def emprunter_media(media_id: int):
	media = trouver_media(media_id)
	if media is None:
		raise HTTPException(status_code=404, detail=MEDIA_INCONNU)

	if not media["disponible"]:
		raise HTTPException(status_code=409, detail="Média déjà emprunté")

	media["disponible"] = False
	emprunt = {
		"id": len(emprunts) + 1,
		"media_id": media_id,
		"retourne": False,
	}
	emprunts.append(emprunt)
	return emprunt


@app.post("/emprunts/{emprunt_id}/retour", dependencies=[Depends(verifier_acces)])
def retourner_emprunt(emprunt_id: int):
	emprunt = trouver_emprunt(emprunt_id)
	if emprunt is None:
		raise HTTPException(status_code=404, detail="Emprunt introuvable")

	if emprunt["retourne"]:
		return emprunt

	media = trouver_media(emprunt["media_id"])
	if media is None:
		raise HTTPException(status_code=404, detail=MEDIA_INCONNU)

	media["disponible"] = True
	emprunt["retourne"] = True
	return emprunt