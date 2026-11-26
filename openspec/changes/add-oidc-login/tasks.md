# Tareas

Cada grupo es un PR (GitHub Flow): rama desde `main`, TDD con tests AAA, CI en verde.

## 1. Base de datos y auditoría (PR 1: `feat/rf-01-base-de-datos`)

- [x] 1.1 Agregar `sqlalchemy[asyncio]`, `psycopg[binary]` y `alembic`, y como dependencias de desarrollo `pytest-asyncio` y `testcontainers[postgres]`, justificadas en el PR; verificar que `uv sync` y `uv run mypy` pasan
- [x] 1.2 Agregar `database_url` a `Settings`, que lee Alembic; verificar que `alembic upgrade head` usa esa URL
- [x] 1.3 Fixture de pytest que levanta `postgres:17-alpine` con testcontainers, aplica las migraciones y deshace cada test en una transacción; verificar con un test que hace `SELECT 1`
- [x] 1.4 Configurar Alembic con `env.py` async y la primera migración con `users`, `user_identities` (único en `issuer` + `subject`), `sessions` (`token_hash`, `user_id`, `created_at`, `expires_at`) y `audit_log`; verificar que `alembic upgrade head` y `alembic downgrade base` corren contra la base de `docker compose`
- [x] 1.5 Trigger que rechaza `UPDATE` y `DELETE` en `audit_log`; verificar con dos tests (actualizar falla, borrar falla) que cubren la spec `security-audit`, requisito "Solo inserción"
- [x] 1.6 Función para registrar eventos de auditoría (`login_succeeded`, `login_denied`, `logout`) que no acepta correo ni tokens; verificar con un test que el evento queda guardado con proveedor, usuario y hora
- [x] 1.7 Actualizar el README (cómo correr las migraciones) y agregar `DATABASE_URL` al CI si hace falta; verificar que el job `backend` pasa en el PR

## 2. Login con Google (PR 2: `feat/rf-01-login-google`)

- [x] 2.1 Agregar `authlib`, `itsdangerous` y `httpx2`, justificadas en el PR, con `httpx2` elegido sobre `httpx` en el ADR-0009; verificar que `uv run mypy` pasa
- [x] 2.2 `AsyncEngine` creado en el lifespan y una dependencia que entrega un `AsyncSession` por petición, con el event loop de psycopg resuelto para `uvicorn` en Windows; verificar con un test que usa `TestClient` como contexto (corre el lifespan) y con `uvicorn` sin `--reload` en Windows
- [x] 2.3 Agregar a `Settings` y a `.env.example` (sin valores reales) `ALLOWED_EMAILS`, `SESSION_SECRET` y `APP_URL`; verificar con un test que `ALLOWED_EMAILS` vacía rechaza todo y que se compara sin mayúsculas
- [x] 2.4 Montar la API bajo `/api` y agregar `SessionMiddleware` (cookie `ccap_oauth`, 10 minutos) solo para el estado del flujo; verificar que `/api/health` responde y que `/docs` sigue apagado por defecto
- [x] 2.5 `GET /api/auth/google/login`: verificar con un test que la redirección lleva `openid email`, `state`, `nonce`, `code_challenge_method=S256` y ningún permiso de correo
- [x] 2.6 `GET /api/auth/google/callback` con ID tokens firmados en el test y el descubrimiento y los JWKS de Google simulados con `httpx2.MockTransport`; verificar los escenarios de la spec: `state` distinto, sin login previo, audiencia ajena, `nonce` distinto, correo no permitido, `email_verified` falso y correo permitido
- [x] 2.7 Identidades y usuario único (diseño, decisión 4); verificar con tests: una identidad conocida con otro correo es el mismo usuario, y una segunda identidad permitida se asocia al usuario existente
- [x] 2.8 Sesión del servidor: token aleatorio, hash en `sessions`, cookie `ccap_session` `HttpOnly`/`Secure`/`SameSite=Lax`/`Path=/`, vencimiento a 12 horas, sesión anterior invalidada y vencidas borradas en cada login; verificar los escenarios de "Sesión segura"
- [x] 2.9 Dependencia `current_user`, `GET /api/auth/me` y `POST /api/auth/logout`, con eventos de auditoría de login y logout; verificar los escenarios de "Consultar la sesión activa", "Cerrar sesión", "Endpoints protegidos" y "Eventos de sesión en la auditoría"
- [x] 2.10 Escribir el ADR-0008 (sesión del lado del servidor y una persona con varias identidades) y actualizar el STRIDE: S-01, S-02 y una amenaza nueva por login con cuentas ajenas, mitigada con `ALLOWED_EMAILS`; verificar que los links del índice de ADR funcionan
- [ ] 2.11 Prueba manual con una cuenta real de Google en modo Testing; verificar que el login lleva a la PWA y que `GET /api/auth/me` devuelve el correo

## 3. Login con Microsoft (PR 3: `feat/rf-01-login-microsoft`)

- [ ] 3.1 Registrar el proveedor Microsoft con el descubrimiento de `consumers`; verificar con un test que la redirección lleva `openid email`, `state`, `nonce` y PKCE
- [ ] 3.2 Callback de Microsoft con ID tokens firmados en el test; verificar el login permitido y que un token con emisor de otro tenant se rechaza sin crear sesión ni usuario
- [ ] 3.3 Actualizar el STRIDE con el riesgo de que el correo de Microsoft no trae `email_verified`; verificar que el documento lo menciona
- [ ] 3.4 Prueba manual con una cuenta personal de Outlook; verificar que la identidad queda asociada al mismo usuario que la de Google

## 4. Pantalla de login en la PWA (PR 4: `feat/rf-01-pantalla-login`)

- [ ] 4.1 Proxy de Vite de `/api` hacia `localhost:8000`; verificar que `pnpm dev` sirve `/api/health`
- [ ] 4.2 Pantalla de login con "Entrar con Google" y "Entrar con Microsoft", y vista con el correo y "Cerrar sesión" cuando hay sesión; verificar con tests de Vitest que la vista cambia según la respuesta de `/api/auth/me`
- [ ] 4.3 Mensaje "Esta cuenta no tiene acceso" cuando la URL trae `login=denied`; verificar con un test de Vitest
- [ ] 4.4 Prueba manual de punta a punta en Chrome sobre `http://localhost:5173`; verificar que la cookie `Secure` se guarda, que el logout funciona y que tras cerrar sesión se vuelve a la pantalla de login

## Seguimiento

- Archivar el cambio con `openspec archive add-oidc-login` cuando estén fusionados los 4 PR.
- Marcar RF-01 como hecho en el PRD.
