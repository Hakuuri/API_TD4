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
