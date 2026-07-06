import sys
from pathlib import Path
from typing import Optional

import strawberry

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))


# Données locales au service GraphQL — même jeu de données de référence que le lot A.
# Choix documenté : le service GraphQL maintient son propre état pour éviter le couplage
# fort entre services. Les emprunts effectués via l'API REST ne sont pas reflétés ici.
_medias: list[dict] = [
    {"id": 1, "titre": "Dune", "type": "livre", "auteur": "Frank Herbert", "annee": 1965, "disponible": True},
    {"id": 2, "titre": "Inception", "type": "dvd", "auteur": "Christopher Nolan", "annee": 2010, "disponible": True},
    {"id": 3, "titre": "The Legend of Zelda: Breath of the Wild", "type": "jeu", "auteur": "Nintendo", "annee": 2017, "disponible": False},
]

_emprunts: list[dict] = []


@strawberry.type
class Media:
    id: int
    titre: str
    type: str
    auteur: str
    annee: int
    disponible: bool


@strawberry.type
class Emprunt:
    id: int
    media_id: int
    retourne: bool


@strawberry.type
class Statistique:
    media_id: int
    titre: str
    nombre_emprunts: int


@strawberry.type
class Query:
    @strawberry.field
    def medias(
        self,
        titre: Optional[str] = None,
        auteur: Optional[str] = None,
        disponible: Optional[bool] = None,
    ) -> list[Media]:
        resultat = _medias
        if titre is not None:
            resultat = [m for m in resultat if titre.lower() in m["titre"].lower()]
        if auteur is not None:
            resultat = [m for m in resultat if auteur.lower() in m["auteur"].lower()]
        if disponible is not None:
            resultat = [m for m in resultat if m["disponible"] == disponible]
        return [Media(**m) for m in resultat]

    @strawberry.field
    def statistiques(self) -> list[Statistique]:
        compteur: dict[int, int] = {}
        for emprunt in _emprunts:
            mid = emprunt["media_id"]
            compteur[mid] = compteur.get(mid, 0) + 1

        top3 = sorted(compteur.items(), key=lambda x: x[1], reverse=True)[:3]

        result = []
        for media_id, count in top3:
            media = next((m for m in _medias if m["id"] == media_id), None)
            if media:
                result.append(Statistique(media_id=media_id, titre=media["titre"], nombre_emprunts=count))
        return result


schema = strawberry.Schema(query=Query)
