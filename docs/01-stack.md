# Stack tecnológico

Restricción: costo cero. Todo corre en local (Windows, Ryzen 7 5800X, 32 GB RAM, RTX 3070 8 GB VRAM).
Cada decisión no obvia tiene su ADR en [docs/adr](adr/README.md).

| Capa | Elección |
|---|---|
| Lenguaje / tooling | Python 3.13, `uv`, `ruff`, `mypy --strict`, `pre-commit` (gitleaks) |
| API | FastAPI, Pydantic v2, `pydantic-settings` |
| Base de datos | Postgres, SQLAlchemy 2 async, `psycopg` 3, Alembic |
| Cola de tareas | Procrastinate (cola en Postgres) |
| Correo | `httpx2` contra Gmail API y Microsoft Graph, detrás de un `Protocol` `EmailProvider` |
| Notificación de correo nuevo | Gmail: Pub/Sub push + respaldo por polling (`history.list`). Outlook: webhooks de Graph |
| OAuth / login | `authlib`, login OIDC con Google o Microsoft, sesión en cookie `HttpOnly` |
| IA | `Protocol` `LLMClient`: Ollama (por defecto) y SDK `anthropic` (opcional, se prueba con mocks) |
| Modelo local | Ollama nativo en Windows (usa la GPU), modelo 7–9B cuantizado Q4; se elige con el set de evaluación |
| Datos personales | Microsoft Presidio + spaCy español + reconocedores de cédula/NIT |
| Cifrado de tokens | AES-GCM (`cryptography`), versión de llave por fila |
| Frontend | TypeScript, Vite, React, `vite-plugin-pwa` |
| Web Push | `pywebpush` + VAPID |
| Tests | `pytest`, `pytest-asyncio`, `httpx2.MockTransport`, `testcontainers`, `vitest` |
| CI | GitHub Actions (repo público): ruff, mypy, pytest, eslint, tsc, gitleaks, CodeQL, Dependabot |
| Entorno local | `docker compose` (Postgres, API, worker) + `cloudflared` para HTTPS público |

## Reglas que impone el costo cero

- El set de evaluación usa solo correos sintéticos (repo público + Ley 1581).
- Ningún secreto en el repo: `.env` ignorado, gitleaks en pre-commit y CI.
- Despliegue fuera de alcance por ahora; la demo es un video en el README.

## Pendiente de verificar

- Si activar Pub/Sub exige cuenta de facturación con tarjeta.
- Vigencia de `watch` de Gmail (~7 días) y de suscripciones de Graph (<3 días).
- Vencimiento de refresh tokens con la app de Google en modo "Testing" (~7 días).
