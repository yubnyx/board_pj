#!/bin/sh
set -e

echo "[entrypoint] Waiting for MySQL at $DB_HOST:$DB_PORT..."
for i in $(seq 1 30); do
  if python -c "from app.database import engine; engine.connect().close()" 2>/dev/null; then
    echo "[entrypoint] MySQL is up."
    break
  fi
  sleep 2
done

echo "[entrypoint] Ensuring tables exist..."
python -c "from app.database import Base, engine; from app import models; Base.metadata.create_all(engine)"

POST_COUNT=$(python -c "from app.database import SessionLocal; from app import models; db=SessionLocal(); print(db.query(models.Post).count()); db.close()")
if [ "$POST_COUNT" = "0" ]; then
  echo "[entrypoint] DB empty — seeding sample posts..."
  python seed.py
else
  echo "[entrypoint] DB has $POST_COUNT posts — skipping seed."
fi

VEC_COUNT=$(python -c "from app import vector; print(vector.get_collection().count())" 2>/dev/null || echo "0")
if [ "$VEC_COUNT" = "0" ]; then
  echo "[entrypoint] Vector index empty — indexing..."
  python index.py
else
  echo "[entrypoint] Vector index has $VEC_COUNT docs — skipping."
fi

echo "[entrypoint] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
