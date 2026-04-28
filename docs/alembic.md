### Init Alembic

```bash
docker-compose exec api_app alembic init alembic
```

### Create Migrations

```bash
docker-compose exec api_app alembic revision --autogenerate -m "Initial migration"
```

### Run Migrations
```bash
docker-compose exec api_app alembic upgrade head
```
or
```bash
docker-compose restart api_app
```

### Refresh Migration
```bash
docker-compose exec api_app alembic downgrade base
```