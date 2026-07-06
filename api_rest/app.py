"""Lot A - API REST : catalogue et emprunts.

Framework : FastAPI, pour rester coherent avec auth_securite et pouvoir brancher
verifier_acces() directement via Depends() sur chaque route.

Repartition au sein de l'equipe :
- POST /medias, PUT /medias/{id}, DELETE /medias/{id} (ci-dessous)
- GET /medias, GET /medias/{id}, POST /medias/{id}/emprunt, POST /emprunts/{id}/retour
  sont a la charge d'un autre membre de l'equipe sur ce meme fichier.
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


# Stockage en memoire partage par toutes les routes de ce service (GET compris).
medias_db: dict[int, Media] = {}
_prochain_id = 1


def _reset_store() -> None:
    """Reinitialise le catalogue. Utilise par les tests pour isoler chaque cas."""
    global _prochain_id
    medias_db.clear()
    _prochain_id = 1


@app.post("/medias", status_code=status.HTTP_201_CREATED, response_model=Media)
def creer_media(
    media: MediaCreation,
    payload: dict = Depends(verifier_acces(role_requis="bibliothecaire")),
):
    global _prochain_id
    nouveau_media = Media(id=_prochain_id, **media.model_dump())
    medias_db[nouveau_media.id] = nouveau_media
    _prochain_id += 1
    return nouveau_media


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
