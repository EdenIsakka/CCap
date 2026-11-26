# Spec Delta

## Purpose

Define quién puede entrar a CCap, cómo inicia y cierra sesión con Google o Microsoft por OIDC, y cómo se protege la sesión.

## ADDED Requirements

### Requirement: Inicio de sesión con Google
El sistema SHALL permitir iniciar sesión con una cuenta de Google por OIDC, pidiendo solo los permisos `openid` y `email`.

#### Scenario: Redirección a Google
- **WHEN** la persona usuaria elige "Entrar con Google"
- **THEN** el sistema la redirige a Google con los permisos `openid` y `email`, un `state` aleatorio, un `nonce` aleatorio y un desafío PKCE S256

#### Scenario: No pide permisos de correo
- **WHEN** el sistema arma la redirección de login
- **THEN** la redirección no incluye `gmail.readonly`, `Mail.Read` ni otros permisos de correo

### Requirement: Inicio de sesión con Microsoft
El sistema SHALL permitir iniciar sesión con una cuenta personal de Microsoft (Outlook.com, Hotmail) por OIDC, pidiendo solo `openid` y `email`. Las cuentas de trabajo o de estudio MUST ser rechazadas.

#### Scenario: Redirección a Microsoft
- **WHEN** la persona usuaria elige "Entrar con Microsoft"
- **THEN** el sistema la redirige al endpoint de cuentas personales de Microsoft con `openid` y `email`, `state`, `nonce` y PKCE S256

#### Scenario: Cuenta de trabajo rechazada
- **WHEN** el callback trae un ID token emitido por un tenant distinto del de cuentas personales
- **THEN** el sistema responde con error, no crea sesión y no crea usuario

### Requirement: Validación del callback
El sistema MUST rechazar el callback si el `state` no coincide con el del navegador que inició el login, o si el ID token falla la validación de firma, emisor, audiencia, vencimiento o `nonce`.

#### Scenario: State distinto
- **WHEN** el callback llega con un `state` que no coincide con el guardado para ese navegador
- **THEN** el sistema responde 400 y no crea sesión

#### Scenario: Callback sin login previo
- **WHEN** el callback llega a un navegador que no inició el login
- **THEN** el sistema responde 400 y no crea sesión

#### Scenario: Login cancelado en el proveedor
- **WHEN** el proveedor vuelve al callback con un error, por ejemplo porque la persona canceló el consentimiento
- **THEN** el sistema no crea sesión y redirige a la PWA indicando que el login se canceló

#### Scenario: ID token con audiencia ajena
- **WHEN** el ID token trae una audiencia distinta del client ID de CCap
- **THEN** el sistema responde con error y no crea sesión

#### Scenario: ID token con nonce distinto
- **WHEN** el `nonce` del ID token no coincide con el enviado al iniciar el login
- **THEN** el sistema responde con error y no crea sesión

### Requirement: Solo entran correos permitidos
El sistema SHALL crear sesión solo si el correo del ID token está en `ALLOWED_EMAILS`, sin distinguir mayúsculas. En Google el correo MUST venir verificado (`email_verified`).

#### Scenario: Correo permitido
- **WHEN** el ID token es válido y su correo está en `ALLOWED_EMAILS`
- **THEN** el sistema crea la sesión y redirige a la PWA

#### Scenario: Correo no permitido
- **WHEN** el ID token es válido pero su correo no está en `ALLOWED_EMAILS`
- **THEN** el sistema no crea sesión ni usuario, registra un login rechazado en la auditoría y redirige a la PWA indicando que el acceso fue rechazado

#### Scenario: Correo de Google sin verificar
- **WHEN** el ID token de Google trae `email_verified` en falso
- **THEN** el sistema no crea sesión y redirige a la PWA indicando que el acceso fue rechazado

#### Scenario: Lista vacía
- **WHEN** `ALLOWED_EMAILS` está vacía o no está definida
- **THEN** el sistema rechaza todo login de la misma forma

### Requirement: Identidad por emisor y sujeto
El sistema SHALL identificar cada cuenta de login por el emisor (`iss`) y el sujeto (`sub`) del ID token, no por el correo. Es una instalación de una sola persona: toda identidad permitida pertenece al mismo usuario.

#### Scenario: Cambio de correo en el proveedor
- **WHEN** una identidad ya conocida vuelve a entrar con otro correo que también está permitido
- **THEN** el sistema la reconoce como el mismo usuario

#### Scenario: Segundo proveedor
- **WHEN** la persona usuaria entra con Microsoft después de haber entrado con Google, ambos con correos permitidos
- **THEN** las dos identidades quedan asociadas al mismo usuario

### Requirement: Sesión segura
El sistema SHALL guardar la sesión en el servidor y entregar al navegador solo un identificador aleatorio en una cookie `HttpOnly`, `Secure` y `SameSite=Lax`. Cada login MUST emitir un identificador nuevo, y la sesión MUST vencer 12 horas después del login.

#### Scenario: Cookie de sesión
- **WHEN** el login termina bien
- **THEN** la respuesta pone una cookie de sesión con `HttpOnly`, `Secure`, `SameSite=Lax` y `Path=/`

#### Scenario: Identificador nuevo en cada login
- **WHEN** un navegador que ya tenía una cookie de sesión vuelve a iniciar sesión
- **THEN** recibe un identificador distinto y el anterior deja de ser válido

#### Scenario: Sesión vencida
- **WHEN** llega una petición con una sesión creada hace más de 12 horas
- **THEN** el sistema responde 401

#### Scenario: Identificador inventado
- **WHEN** llega una petición con una cookie de sesión que el servidor no emitió
- **THEN** el sistema responde 401

### Requirement: Consultar la sesión activa
El sistema SHALL exponer un endpoint que, con una sesión válida, devuelve el correo y el proveedor con que se inició la sesión, y sin sesión responde 401.

#### Scenario: Con sesión
- **WHEN** la PWA consulta la sesión activa con una cookie válida
- **THEN** recibe 200 con el correo y el proveedor

#### Scenario: Sin sesión
- **WHEN** la PWA consulta la sesión activa sin cookie
- **THEN** recibe 401

### Requirement: Cerrar sesión
El sistema SHALL permitir cerrar la sesión: la invalida en el servidor y borra la cookie del navegador.

#### Scenario: Logout
- **WHEN** la persona usuaria cierra sesión
- **THEN** la sesión deja de ser válida en el servidor, la cookie se borra y la siguiente petición con ese identificador recibe 401

### Requirement: Endpoints protegidos
Todo endpoint de la API MUST exigir una sesión válida, salvo health, el inicio de login y el callback (STRIDE E-02).

#### Scenario: Petición sin sesión
- **WHEN** llega una petición sin sesión a un endpoint que no es health, login ni callback
- **THEN** el sistema responde 401

### Requirement: Pantalla de inicio de sesión
La PWA SHALL mostrar una pantalla de login con "Entrar con Google" y "Entrar con Microsoft" a quien no tiene sesión, y la app a quien sí la tiene.

#### Scenario: Sin sesión
- **WHEN** alguien abre la PWA sin sesión
- **THEN** ve la pantalla de login con las dos opciones

#### Scenario: Con sesión
- **WHEN** alguien abre la PWA con una sesión válida
- **THEN** ve la app con su correo y la opción de cerrar sesión

#### Scenario: Login rechazado
- **WHEN** el login vuelve con correo no permitido
- **THEN** la PWA muestra que esa cuenta no tiene acceso, sin detalles técnicos
