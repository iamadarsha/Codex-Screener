# Local development with Apple Container

The backend (`apps/api`) is built as a standard OCI image (`apps/api/Dockerfile`).
On Apple Silicon Macs, Docker Desktop is **not required** — Apple's `container`
CLI runs the same image locally as a native Linux VM, and the same ARM64 image
is what eventually runs on the Oracle Cloud ARM VM in production. The Dockerfile
is the image recipe either way; `container` is just a different local runtime
than `docker`.

## Prerequisites

- Apple Silicon Mac, macOS with the `container` CLI installed (`brew install --cask container` or via Apple's installer — see https://github.com/apple/container).
- Run `container system start` once per login session before building/running.
- No Docker Desktop needed. `docker-compose.yml` at the repo root still works if you prefer Docker Desktop for Postgres/Redis — `container` is only used here for the API image itself.

## Image build

```bash
scripts/container-build.sh
```

Builds `apps/api/Dockerfile` and tags it `breakoutscan-api:local` (override with `IMAGE_TAG=...`).

## Local environment setup

Copy `.env.example` to `apps/api/.env` and fill in at least `REDIS_URL` (a local Redis is easiest via `docker compose up redis` or `brew services start redis`). Everything else degrades gracefully if unset (see `apps/api/app/main.py`'s lifespan — Redis absence logs a warning and the app still starts).

## Service startup

```bash
scripts/container-run.sh
```

Starts the container in the foreground, publishing port 8001, loading `apps/api/.env` if present. Override the port with `PORT=8002 scripts/container-run.sh`.

## Logs

```bash
container logs -f breakoutscan-api
```

## Shell access

```bash
container exec -it breakoutscan-api /bin/sh
```

## Test commands

```bash
scripts/container-test.sh
```

Hits `/health` on the running container (or starts one itself if none is running) and asserts a JSON response with a `status` field.

## Cleanup

```bash
container stop breakoutscan-api
container rm breakoutscan-api        # if not run with --rm
container images rm breakoutscan-api:local
```

## ARM64 behavior notes

- `python:3.12-slim` is a multi-arch base image — no changes needed for ARM64.
- `numpy`/`pandas`/`pandas-ta` are installed with `--prefer-binary` in the Dockerfile specifically to use pre-built ARM64 wheels rather than compiling from source, which is both faster and avoids needing a C toolchain in the image.
- The same image (`apps/api/Dockerfile`, unmodified) is intended to run on an Oracle Cloud `VM.Standard.A1.Flex` (Ampere ARM) instance — no separate Dockerfile or build args needed for production.
