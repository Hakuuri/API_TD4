"""Configuration partagee par les 3 lots (contrat d'interface, section 4.4 du sujet).

SECRET_KEY et ALGORITHM doivent rester strictement identiques dans auth_securite,
api_rest et api_graphql : c'est ce qui permet a un token emis par le lot C d'etre
accepte tel quel par les lots A et B.
"""

import os

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-a-ne-jamais-utiliser-en-production")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
