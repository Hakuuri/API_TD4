## Structure

- `auth_securite/` - Lot C : authentification (register/login/refresh) et module
  de verification JWT partage (`verification.py`), importe par les 2 autres lots.
- `api_rest/` - Lot A : API REST du catalogue et des emprunts.
- `api_graphql/` - Lot B : API GraphQL de recherche et statistiques.
- `common/config.py` - SECRET_KEY et algorithme JWT partages entre les 3 services.

## Installation

Depuis la racine du depot :

```bash
python -m venv .venv
.venv\Scripts\activate        # PowerShell : .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Lancer les services (developpement)

Toujours depuis la racine du depot, pour que les imports `common.*` et
`auth_securite.*` se resolvent correctement :

```bash
# Service d'authentification (port 8000)
python -m uvicorn auth_securite.app:app --reload --port 8000

# API REST du catalogue (port 8001)
python -m uvicorn api_rest.app:app --reload --port 8001
```

## Lancer les tests

```bash
pytest
```

## Authentification

1. `POST /auth/register` avec `{"username", "password", "role": "usager"|"bibliothecaire"}`
2. `POST /auth/login` renvoie `{"access_token", "refresh_token"}`
3. Utiliser l'access_token dans l'en-tete `Authorization: Bearer <token>` sur les
   routes protegees de `api_rest` et `api_graphql`.
4. `POST /auth/refresh` avec `{"refresh_token"}` renvoie un nouvel access_token.
