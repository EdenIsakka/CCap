# ADR-0008: Sesión del lado del servidor y una persona con varias identidades

- Estado: Aceptado
- Fecha: 2026-11-26

## Contexto

RF-01 pide iniciar sesión con Google o Microsoft. El STRIDE exige poder invalidar la sesión (S-02) y el PRD define una instalación para una sola persona, que tiene una cuenta de Gmail y una de Outlook.

## Decisión

1. **Sesión en Postgres.** La cookie `ccap_session` (`HttpOnly`, `Secure`, `SameSite=Lax`) lleva un token aleatorio de 32 bytes. La tabla `sessions` guarda solo su SHA-256, el usuario, la identidad con que se entró y el vencimiento (12 horas). Cerrar sesión borra la fila. Cada login borra la sesión anterior de ese navegador y las vencidas.
2. **Estado del flujo OAuth en una cookie firmada aparte** (`ccap_oauth`, 10 minutos, `SessionMiddleware`). Solo guarda `state`, `nonce` y el verificador de PKCE mientras dura el login, que es como trabaja `authlib`.
3. **Un usuario, varias identidades.** Cada cuenta de login es una fila de `user_identities`, identificada por emisor + sujeto del ID token, no por correo. Toda identidad permitida (`ALLOWED_EMAILS`) se asocia al único usuario de la instalación.

## Alternativas

| Opción | Por qué no |
|---|---|
| Sesión en una cookie firmada (sin tabla) | No se puede revocar antes de que venza |
| Estado del flujo OAuth en una tabla propia | Más código para lo mismo; `authlib` ya resuelve la validación del callback |
| Un usuario por identidad | Entrar con Microsoft mostraría otros datos que entrar con Google |
| Identificar por correo | El correo puede cambiar en el proveedor; emisor + sujeto no |

## Consecuencias

- El logout invalida la sesión en el momento, y quien lea la base no obtiene tokens usables.
- La cookie `ccap_oauth` está firmada pero no cifrada: el navegador puede leer el verificador de PKCE. Es aceptable, porque PKCE protege contra quien intercepta el código, no contra el navegador que inició el login.
- La regla "un solo usuario" vive en un solo lugar (`_identity_for` en `ccap/auth.py`). Todo lo demás filtra por `user_id`, así que pasar a multiusuario solo cambia ese paso.
