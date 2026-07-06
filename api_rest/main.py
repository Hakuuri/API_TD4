from fastapi import FastAPI, HTTPException, Query


app = FastAPI()


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


@app.get("/medias")
def lire_medias(type: str | None = None, disponibilite: bool | None = Query(default=None)):
	resultat = medias

	if type is not None:
		resultat = [media for media in resultat if media["type"] == type]

	if disponibilite is not None:
		resultat = [media for media in resultat if media["disponible"] == disponibilite]

	return resultat


@app.get("/medias/{media_id}")
def lire_media(media_id: int):
	for media in medias:
		if media["id"] == media_id:
			return media

	raise HTTPException(status_code=404, detail="Média introuvable")