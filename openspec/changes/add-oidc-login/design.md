# Diseño

## Contexto

El backend tiene hoy solo `/health`, `Settings` y FastAPI con `/docs` apagado fuera de desarrollo. No hay base de datos conectada. Postgres corre en `docker compose` en `127.0.0.1:5433`. El stack ([docs/01-stack.md](../../../docs/01-stack.md)) ya eligió `authlib`, SQLAlchemy 2 async, `psycopg` 3 y Alembic. El motivo del cambio está en `proposal.md` y el comportamiento en `specs/`.

Restricciones que vienen del repo:

- Toda consulta se filtra por el `user_id` de la sesión (CLAUDE.md, regla 5).
- Puertos solo en fronteras externas: el proveedor de identidad es una, pero `authlib` ya la abstrae (ver decisión 2).
- Cero costo: todo en local, con `http://localhost` como redirect URI.

## Objetivos / No objetivos

**Objetivos**

- Login de punta a punta con Google y Microsoft, probado sin red con `httpx2.MockTransport` y ID tokens firmados en el test.
- Un patrón de base de datos (sesión async por petición, migraciones, tests con Postgres real) que RF-02 en adelante reutilicen.

**No objetivos**

- Pedir permisos de correo o guardar tokens OAuth. Eso es RF-02: en este cambio no se persiste ningún access token ni refresh token.
- Multiusuario, roles o administración de `ALLOWED_EMAILS` desde la PWA.
- Renovar la sesión deslizando su vencimiento. Vence a las 12 horas, sin excepciones.
- Limitar la tasa de intentos de login. La API solo escucha en localhost (STRIDE, hallazgo principal).

## Decisiones

### 1. Sesión del lado del servidor en Postgres

La cookie `ccap_session` lleva un token aleatorio de 32 bytes (`secrets.token_urlsafe`). La tabla `sessions` guarda solo el SHA-256 del token, el `user_id`, `created_at` y `expires_at`. Cerrar sesión borra la fila.

- **Por qué:** el logout invalida la sesión de verdad, y quien lea la base no obtiene tokens usables (STRIDE S-02).
- **Alternativa descartada:** cookie firmada con los datos de la sesión (`SessionMiddleware` de Starlette). No se puede revocar antes de que venza.
- Va en un ADR nuevo (0008), junto con la decisión 4.

### 2. `authlib` con su cliente de Starlette para el flujo OIDC

`authlib` lee el documento de descubrimiento de cada proveedor, genera `state` y `nonce`, hace PKCE S256 y valida firma, `iss`, `aud`, `exp` y `nonce` del ID token. Su cliente de Starlette guarda `state`, `nonce` y el verificador de PKCE en `request.session`, que exige `SessionMiddleware`.

- `SessionMiddleware` se usa solo para ese estado temporal del flujo, en una cookie aparte (`ccap_oauth`, firmada con `SESSION_SECRET`, `max_age` de 10 minutos, `same_site=lax`, `https_only`). La sesión autenticada es la de la decisión 1.
- **Por qué:** es el camino documentado de `authlib`, con poco código propio en la parte más delicada (validar el ID token).
- **Alternativas descartadas:** guardar el estado del flujo en una tabla propia, que es más código para el mismo resultado; o escribir el flujo con `httpx` a mano, que obliga a validar JWT y JWKS por cuenta propia.
- **Riesgo:** la cookie `ccap_oauth` está firmada pero no cifrada, así que el navegador puede leer el verificador de PKCE. Es aceptable porque PKCE protege contra quien intercepta el código, no contra el propio navegador que inició el login.

### 3. Microsoft solo con cuentas personales

Se usa el descubrimiento de `https://login.microsoftonline.com/consumers/v2.0`. Su emisor es fijo (el tenant de cuentas personales), así que la validación normal de `iss` ya rechaza las cuentas de trabajo.

- **Alternativa descartada:** el tenant `common`, cuyo emisor depende del tenant de cada token y exige una validación propia.

### 4. Identidad: un usuario, varias identidades

Las tablas son `users` (`id`) y `user_identities` (`issuer`, `subject`, `user_id`, `email`, con único en `issuer` + `subject`). En el callback:

1. Si `(iss, sub)` ya existe, se usa su usuario y se actualiza el `email`.
2. Si no existe y el correo está permitido, la identidad se asocia al único usuario. Si todavía no hay usuario, se crea.

- **Por qué:** el PRD define una instalación para una sola persona, que tiene Gmail y Outlook. Sin esto, entrar con Microsoft mostraría otros datos que entrar con Google.
- **Riesgo:** la regla "un solo usuario" vive en el código del callback. El resto del sistema sigue filtrando por `user_id`, así que pasar a multiusuario solo cambia ese paso.

### 5. Lista de acceso en la configuración

`ALLOWED_EMAILS` es una lista separada por comas en `Settings`, que se normaliza a minúsculas. Si está vacía, nadie entra (falla cerrado). El correo se revisa en cada login, no solo en el primero, así que quitar un correo de la lista corta el acceso desde el siguiente login.

### 6. Auditoría de solo inserción con un trigger

`audit_log` tiene `id`, `created_at`, `event` (texto con valores fijos), `provider`, `user_id` (opcional) y `detail` (texto corto, por ejemplo el motivo del rechazo). Un trigger de Postgres rechaza `UPDATE` y `DELETE`.

- `user_id` no tiene llave foránea a `users`. Así, el borrado de la cuenta (RF-09) puede borrar al usuario sin tocar la auditoría.
- **Por qué un trigger:** la app usa un único rol de Postgres, así que quitarle permisos (`REVOKE`) a ese rol no sirve. El trigger se prueba con un test.

### 7. Base de datos: sesión async por petición y tests con Postgres real

Se crea un `AsyncEngine` al arrancar (lifespan) y una dependencia de FastAPI entrega un `AsyncSession` por petición. Alembic maneja las migraciones con un `env.py` async.

- Los tests usan `testcontainers` con `postgres:17-alpine`, la misma imagen de `compose.yaml`. Cada test corre dentro de una transacción que se deshace al final.
- **Por qué Postgres real y no SQLite:** el trigger, los tipos y Procrastinate (más adelante) son de Postgres.

### 8. Mismo origen en desarrollo con el proxy de Vite

La PWA llama a `/api/*`, y Vite reenvía esas peticiones al backend en `localhost:8000`. La API se monta bajo `/api`.

- `APP_URL` (por ejemplo `http://localhost:5173`) arma los redirect URI (`{APP_URL}/api/auth/{google|microsoft}/callback`) y el destino tras el login. No se usa `request.url_for`, porque detrás del proxy daría el host del backend.
- **Por qué:** la cookie queda en el mismo origen que la PWA, sin CORS y con `SameSite=Lax` sin excepciones.

### 9. Endpoints

- `GET /api/auth/{provider}/login` redirige al proveedor.
- `GET /api/auth/{provider}/callback` valida, crea la sesión y redirige (303) a `APP_URL`. Si el correo no está permitido, redirige a `APP_URL/?login=denied`: el callback es una navegación del navegador, así que una página 403 de la API dejaría a la persona fuera de la PWA. Un `state` inválido o un ID token inválido responden 400 sin redirigir, porque indican un ataque o un error, no una cuenta ajena.
- `GET /api/auth/me` devuelve 200 con `{email, provider}`, o 401.
- `POST /api/auth/logout` borra la sesión y devuelve 204. Es `POST`, así que `SameSite=Lax` impide que otro sitio dispare el logout.
- Una dependencia `current_user` lee la cookie, busca el hash, revisa `expires_at` y devuelve el usuario o responde 401. Todo router nuevo la usa por defecto.

## Riesgos / compromisos

- [El correo de Microsoft no trae `email_verified`] → En cuentas personales, el correo es el nombre de inicio de sesión de la cuenta. Se acepta y queda anotado en el STRIDE.
- [La cookie `Secure` en `http://localhost`] → Chrome y Firefox la aceptan porque localhost es un contexto seguro. Se verifica a mano en el PR 4.
- [Los tests de base de datos dependen de Docker] → Docker ya está en el equipo local y en los runners `ubuntu-latest`. Si falta Docker, los tests fallan con un mensaje claro en vez de saltarse.
- [`authlib` 1.9 usa `httpx2` sin declararlo, y `respx` no lo intercepta] → `httpx2` pasa a dependencia de runtime y los tests simulan HTTP con `httpx2.MockTransport` (ADR-0009).
- [Las sesiones vencidas se acumulan en la tabla] → Se borran en cada login. No hace falta un job aparte para una sola persona.

## Plan de despliegue

No hay producción. Cada PR corre `alembic upgrade head` contra la base local. Para revertir, `alembic downgrade` de la revisión del PR.
