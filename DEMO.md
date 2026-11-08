# Playback Gateway — Demo

A small FastAPI service that manages playback sessions (play / pause / expire).

Every request is "authenticated" by middleware as user `1`, so no auth headers
or user ids are needed. Sessions are kept in memory and reset on restart.

## Run

```bash
uv sync
uv run fastapi dev main.py
```

Interactive docs: http://127.0.0.1:8000/docs

## Walkthrough

### 1. Start playing a song

```bash
curl -s -X POST localhost:8000/api/play \
  -H 'Content-Type: application/json' \
  -d '{"device_id": "device_123", "song_id": 42}'
```

```json
{"session_id": 1, "user_id": 1, "timestamp": 1730000000, "device_id": "device_123", "status": "active", "song_id": 42}
```

### 2. Pause it

```bash
curl -s -X POST localhost:8000/api/pause \
  -H 'Content-Type: application/json' \
  -d '{"session_id": 1}'
```

`status` becomes `"paused"`.

### 3. Pausing again is rejected (409)

```bash
curl -s -X POST localhost:8000/api/pause \
  -H 'Content-Type: application/json' \
  -d '{"session_id": 1}'
```

```json
{"detail": "Cannot pause a paused session"}
```

### 4. Expire the session

```bash
curl -s -X POST localhost:8000/api/expire \
  -H 'Content-Type: application/json' \
  -d '{"session_id": 1}'
```

`status` becomes `"expired"`. Expiring again returns 409.

### 5. Unknown session (404)

```bash
curl -s -X POST localhost:8000/api/expire \
  -H 'Content-Type: application/json' \
  -d '{"session_id": 999}'
```

```json
{"detail": "Session not found"}
```

## Endpoints

| Method | Path          | Body                     | Result                         |
|--------|---------------|--------------------------|--------------------------------|
| POST   | `/api/play`   | `{device_id, song_id}`   | New `active` session           |
| POST   | `/api/pause`  | `{session_id}`           | Session set to `paused`        |
| POST   | `/api/expire` | `{session_id}`           | Session set to `expired`       |

Session status flow: `active` → `paused`, and `active`/`paused` → `expired`.

## Talking points

- Auth is stubbed in middleware (`main.py`); swap it for real auth without touching the routes.
- Services (`services.py`) hold the state and rules; routes stay thin.
- Next steps: persistent storage, session expiry timestamps, per-plan concurrent stream limits.
