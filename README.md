Настройки.

1) Необходимо запольнить .env с параметрами:

DATABASE_NAME
DATABASE_USER
DATABASE_PASS
DATABASE_PORT
DATABASE_HOST

JWT_SECRET
RESET_PASS_SECRET

RABBIT_ADMIN=admin
RABBIT_ADMIN_PASS=admin
Так как в кастомном контейнере ребита вшит пользователь admin:admin с правами админа, далее можно переопределить, если нужно.




