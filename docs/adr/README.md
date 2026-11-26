# Registro de decisiones de arquitectura (ADR)

Un ADR por decisión no obvia. Formato: Contexto, Decisión, Alternativas, Consecuencias. Un ADR aceptado no se edita: si la decisión cambia, se escribe uno nuevo que lo reemplaza y el viejo pasa a "Reemplazado por ADR-XXXX".

| ADR | Decisión | Estado |
|---|---|---|
| [0001](0001-cola-en-postgres.md) | Cola de tareas en Postgres (Procrastinate) | Aceptado |
| [0002](0002-httpx-en-vez-de-sdks.md) | `httpx` directo en vez de los SDKs de Google y Microsoft | Aceptado; librería reemplazada por ADR-0009 |
| [0003](0003-ollama-por-defecto-claude-opcional.md) | Ollama por defecto, Claude opcional | Aceptado |
| [0004](0004-polling-en-mvp-push-en-fase-2.md) | Polling en el MVP, push en la fase 2 | Aceptado |
| [0005](0005-cifrado-de-tokens-aes-gcm.md) | Cifrado de tokens OAuth con AES-GCM | Aceptado |
| [0006](0006-un-correo-por-llamada.md) | Un correo por llamada a la IA | Aceptado |
| [0007](0007-eleccion-del-modelo-local.md) | Elección del modelo local | Propuesto |
| [0008](0008-sesion-en-servidor-y-una-persona.md) | Sesión del lado del servidor y una persona con varias identidades | Aceptado |
| [0009](0009-httpx2-en-vez-de-httpx.md) | `httpx2` en vez de `httpx` | Aceptado |
