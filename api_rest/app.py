"""Lot A - API REST : catalogue et emprunts.

Framework : FastAPI, pour rester coherent avec auth_securite et pouvoir brancher
verifier_acces() directement via Depends() sur chaque route.

Fichier fusionne a partir de deux contributions :
- POST /medias, PUT /medias/{id}, DELETE /medias/{id}
- GET /medias, GET /medias/{id}, POST /medias/{id}/emprunt, POST /emprunts/{id}/retour
  (logique initialement ecrite dans api_rest/main.py contre un bouchon verifier_acces,
  reportee ici et adaptee au contrat reel : verifier_acces() est une factory, il faut
  l'appeler pour obtenir la dependance : Depends(verifier_acces()) et non Depends(verifier_acces)).
"""

from enum import Enum

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from auth_securite.verification import verifier_acces

app = FastAPI(title="Mediatheque augmentee - API REST")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc: RequestValidationError):
    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.errors()})


class TypeMedia(str, Enum):
    livre = "livre"
    dvd = "dvd"
    jeu = "jeu"


class Media(BaseModel):
    id: int
    titre: str
    type: TypeMedia
    auteur: str
    annee: int
    disponible: bool = True


class MediaCreation(BaseModel):
    titre: str
    type: TypeMedia
    auteur: str
    annee: int
    disponible: bool = True


class MediaModification(BaseModel):
    titre: str | None = None
    type: TypeMedia | None = None
    auteur: str | None = None
    annee: int | None = None
    disponible: bool | None = None


class Emprunt(BaseModel):
    id: int
    media_id: int
    retourne: bool = False


# Stockage en memoire partage par toutes les routes de ce service.
medias_db: dict[int, Media] = {}
emprunts_db: dict[int, Emprunt] = {}
_prochain_id = 1
_prochain_emprunt_id = 1


def _reset_store() -> None:
    """Reinitialise le catalogue et les emprunts. Utilise par les tests pour isoler chaque cas."""
    global _prochain_id, _prochain_emprunt_id
    medias_db.clear()
    emprunts_db.clear()
    _prochain_id = 1
    _prochain_emprunt_id = 1


def _peupler_donnees_demo() -> None:
    """Jeu de donnees de demarrage pour les tests manuels (uvicorn). Sans effet sur les
    tests automatises, qui appellent _reset_store() avant chaque cas."""
    for media in (
        MediaCreation(titre="Dune", type=TypeMedia.livre, auteur="Frank Herbert", annee=1965, disponible=True),
        MediaCreation(
            titre="Inception", type=TypeMedia.dvd, auteur="Christopher Nolan", annee=2010, disponible=True
        ),
        MediaCreation(
            titre="The Legend of Zelda: Breath of the Wild",
            type=TypeMedia.jeu,
            auteur="Nintendo",
            annee=2017,
            disponible=False,
        ),
    ):
        creer_media_interne(media)


def creer_media_interne(media: MediaCreation) -> Media:
    global _prochain_id
    nouveau_media = Media(id=_prochain_id, **media.model_dump())
    medias_db[nouveau_media.id] = nouveau_media
    _prochain_id += 1
    return nouveau_media


@app.get("/medias", response_model=list[Media])
def lister_medias(
    type: TypeMedia | None = None,
    disponible: bool | None = None,
    payload: dict = Depends(verifier_acces()),
):
    resultat = list(medias_db.values())
    if type is not None:
        resultat = [media for media in resultat if media.type == type]
    if disponible is not None:
        resultat = [media for media in resultat if media.disponible == disponible]
    return resultat


@app.get("/medias/{media_id}", response_model=Media)
def lire_media(media_id: int, payload: dict = Depends(verifier_acces())):
    media = medias_db.get(media_id)
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media introuvable")
    return media


@app.post("/medias", status_code=status.HTTP_201_CREATED, response_model=Media)
def creer_media(
    media: MediaCreation,
    payload: dict = Depends(verifier_acces(role_requis="bibliothecaire")),
):
    return creer_media_interne(media)


@app.put("/medias/{media_id}", response_model=Media)
def modifier_media(
    media_id: int,
    modification: MediaModification,
    payload: dict = Depends(verifier_acces(role_requis="bibliothecaire")),
):
    media_existant = medias_db.get(media_id)
    if media_existant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media introuvable")

    donnees_modifiees = modification.model_dump(exclude_unset=True)
    media_maj = media_existant.model_copy(update=donnees_modifiees)
    medias_db[media_id] = media_maj
    return media_maj


@app.delete("/medias/{media_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_media(
    media_id: int,
    payload: dict = Depends(verifier_acces(role_requis="bibliothecaire")),
):
    if media_id not in medias_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media introuvable")
    del medias_db[media_id]


@app.post("/medias/{media_id}/emprunt", status_code=status.HTTP_201_CREATED, response_model=Emprunt)
def emprunter_media(media_id: int, payload: dict = Depends(verifier_acces())):
    global _prochain_emprunt_id

    media = medias_db.get(media_id)
    if media is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media introuvable")
    if not media.disponible:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Media deja emprunte")

    emprunt = Emprunt(id=_prochain_emprunt_id, media_id=media_id)
    emprunts_db[emprunt.id] = emprunt
    _prochain_emprunt_id += 1
    medias_db[media_id] = media.model_copy(update={"disponible": False})
    return emprunt


@app.post("/emprunts/{emprunt_id}/retour", response_model=Emprunt)
def retourner_emprunt(emprunt_id: int, payload: dict = Depends(verifier_acces())):
    emprunt = emprunts_db.get(emprunt_id)
    if emprunt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Emprunt introuvable")

    if not emprunt.retourne:
        emprunt = emprunt.model_copy(update={"retourne": True})
        emprunts_db[emprunt_id] = emprunt
        media = medias_db.get(emprunt.media_id)
        if media is not None:
            medias_db[emprunt.media_id] = media.model_copy(update={"disponible": True})

    return emprunt


_peupler_donnees_demo()
