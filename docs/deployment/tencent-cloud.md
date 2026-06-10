# 腾讯云部署 Runbook

## Services

- FastAPI app: `xiaoman-web`
- PostgreSQL: `xiaoman-db`

## First Deploy

```bash
docker compose up -d --build
docker compose exec web alembic upgrade head
docker compose exec web pytest -v
```

## Daily Backup

```bash
mkdir -p backups
docker compose exec db pg_dump -U xiaoman xiaoman > backups/xiaoman-$(date +%F).sql
```

## Manual T+1 Update

```bash
docker compose exec web python -m app.jobs.update_prices
```

## Health Check

```bash
curl -f http://127.0.0.1:8000/health
```

## Recovery Notes

1. 数据更新失败时，先检查 `docker compose logs web`。
2. 数据库恢复前先停止 Web：`docker compose stop web`。
3. 恢复完成后运行 `docker compose exec web alembic upgrade head`。
