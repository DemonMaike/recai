

import uuid
from fastapi_users import FastAPIUsers

from auth.manager import get_user_manager
from auth.utils import auth_backand

from models import User


fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backand],
)
current_user = fastapi_users.current_user()
admin = fastapi_users.current_user(superuser=True)
