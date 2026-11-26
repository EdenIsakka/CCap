# Propuesta: inicio de sesión con Google o Microsoft (RF-01)

## Por qué

Hoy la API no sabe quién la usa. Todo lo que viene después necesita una sesión autenticada: conectar cuentas de correo (RF-02), el resumen, el export y el borrado. Además, el STRIDE (E-02) exige sesión en todos los endpoints, salvo login, callback y health. RF-01 es la base de todo eso.

## Qué cambia

- Login con Google y con Microsoft (solo cuentas personales) por OIDC. Solo pide `openid` y `email`; los permisos de correo llegan con RF-02.
- El callback está protegido contra CSRF y contra la inyección de códigos robados: usa `state`, PKCE y `nonce`, y valida el emisor, la audiencia y la firma del ID token (STRIDE S-01).
- Solo entran los correos de `ALLOWED_EMAILS`. Con cualquier otro correo no se crea sesión: vuelve a la PWA con "acceso rechazado" y queda en el registro de auditoría.
- La identidad se ata al emisor y al sujeto del ID token, no al correo. Es una instalación de una sola persona: todas las identidades permitidas pertenecen al mismo usuario.
- Sesión del lado del servidor, guardada en Postgres. La cookie es `HttpOnly`, `Secure` y `SameSite=Lax`, el ID de sesión es nuevo en cada login y la sesión vence a las 12 horas (STRIDE S-02).
- Cerrar sesión, y un endpoint que dice quién tiene la sesión activa.
- Registro de auditoría de solo inserción con los eventos de login, login rechazado y logout (RS-11, STRIDE R-01).
- Primera base de datos del proyecto: SQLAlchemy async, Alembic y las tablas `users`, `user_identities`, `sessions` y `audit_log`.
- La PWA muestra la pantalla de login a quien no tiene sesión.

Entrega en 4 PRs: base de datos, login con Google, login con Microsoft y pantalla de login.

## Capacidades

### Capacidades nuevas

- `user-auth`: quién puede entrar, cómo inicia y cierra sesión, y cómo se protege la sesión.
- `security-audit`: el registro de solo inserción de eventos de seguridad. RF-02 y RF-09 le agregarán eventos después.

### Capacidades modificadas

Ninguna: todavía no hay specs.

## Impacto

- **Backend:** módulos nuevos de base de datos, autenticación y auditoría, y rutas `/auth/*`. Una dependencia que exige sesión para los endpoints protegidos.
- **Dependencias nuevas** (se justifican en cada PR): `sqlalchemy[asyncio]`, `psycopg[binary]`, `alembic`, `authlib`, `itsdangerous`. Para tests: `pytest-asyncio`, `respx`, `testcontainers[postgres]`.
- **Configuración:** variables nuevas en `.env.example`: `ALLOWED_EMAILS`, `SESSION_SECRET` y `APP_URL`.
- **Frontend:** pantalla de login y un proxy de Vite hacia la API, para que la cookie sea del mismo origen.
- **Docs:** un ADR nuevo para las sesiones del lado del servidor y la identidad única; el STRIDE se actualiza (S-01, S-02 y una amenaza nueva por cuentas ajenas).
- **CI:** los tests de base de datos necesitan Docker, que ya está en los runners de GitHub.
