import sys
from pathlib import Path

# FastAPI est choisi pour sa compatibilité native avec Strawberry et sa cohérence
# avec l'API REST du lot A — même framework, même mécanisme Depends() pour le JWT.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from fastapi import Depends, FastAPI
from strawberry.fastapi import GraphQLRouter

from auth_securite.verification import verifier_acces
from api_graphql.schema import schema

app = FastAPI(title="Médiathèque — API GraphQL")

graphql_router = GraphQLRouter(schema)
app.include_router(graphql_router, prefix="/graphql", dependencies=[Depends(verifier_acces)])
