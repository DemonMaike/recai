from fastapi_users.authentication import AuthenticationBackend, JWTStrategy
from fastapi_users.authentication import CookieTransport
from config import JWT_SECRET


SECRET = JWT_SECRET
cookie_transport = CookieTransport(cookie_secure=False,
                                   cookie_httponly=True)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backand = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)
