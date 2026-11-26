# PRD: Resumen de correos (PWA)

Estado: borrador v1, pendiente de revisión.

## 1. Usuario y problema

**Usuario:** una sola persona (quien desarrolla el proyecto), con una cuenta de Gmail y una de Outlook. El modelo de datos es multiusuario, pero solo hay un usuario real. Por eso la app de Google se queda en modo "Testing" y no necesita verificación.

**Problema:**
- Llega demasiado correo para revisarlo uno por uno.
- Lo importante (trabajo) queda enterrado entre promociones y spam.

**Idioma:** los correos llegan en español y en inglés. El clasificador, la detección de datos personales y el set de evaluación deben cubrir los dos.

## 2. Alcance

### MVP
- Conectar una cuenta de Gmail y una de Outlook por OAuth.
- Procesar solo el correo que llega **después** de conectar la cuenta (sin historial).
- Detectar correo nuevo por **polling** (sin Pub/Sub ni webhooks).
- Clasificar cada correo en: **spam, trabajo, finanzas y trámites, notificaciones, otros**.
- Resumen diario: una notificación **Web Push a la hora que elija la persona usuaria**. Al tocarla se abre la PWA con el resumen agrupado por categoría.

### Fase 2
- Correo esperado: la persona usuaria indica remitente o empresa y asunto, y recibe un push apenas llega. Esta fase trae Gmail Pub/Sub y los webhooks de Graph.

### Fuera de alcance
- Actuar sobre los correos (marcar leído, archivar, responder, borrar).
- Procesar el historial anterior a la conexión.
- Más de un usuario real, registro abierto y verificación de Google.
- Despliegue en la nube.
- Adjuntos: no se descargan ni se analizan; solo se registra que existen.

## 3. Requisitos funcionales

| ID | Requisito |
|---|---|
| RF-01 | La persona usuaria inicia sesión con Google o Microsoft (OIDC). |
| RF-02 | La persona usuaria conecta y desconecta una cuenta de Gmail y una de Outlook. Al desconectar se revoca el token y se borra. |
| RF-03 | Un job hace polling de cada cuenta conectada cada 15 minutos y encola los correos nuevos. |
| RF-04 | El worker descarga cada correo, le quita los datos personales, lo clasifica en una de las 5 categorías y genera una línea de resumen. Descarta el cuerpo al terminar. |
| RF-05 | Se guardan solo metadatos (remitente, asunto, fecha, proveedor, ID del correo, categoría) y la línea de resumen. |
| RF-06 | La persona usuaria elige la hora del resumen diario. A esa hora recibe un Web Push. Si no hubo correos nuevos, no se envía. |
| RF-07 | La PWA muestra el resumen agrupado por categoría: remitente, asunto, resumen y un enlace que abre el correo en Gmail u Outlook. |
| RF-08 | La persona usuaria corrige la categoría de un correo desde la PWA. La corrección se guarda como etiqueta. |
| RF-09 | La persona usuaria exporta todos sus datos (JSON) y borra su cuenta con todos sus datos. |
| RF-10 | Los metadatos y resúmenes se borran solos a los 30 días. |

## 4. Requisitos de seguridad y cumplimiento

| ID | Requisito |
|---|---|
| RS-01 | Permisos OAuth de solo lectura: `gmail.readonly` y `Mail.Read` + `offline_access`. Ningún permiso de escritura. |
| RS-02 | Tokens OAuth cifrados con AES-GCM. La llave nunca está en la base de datos ni en el repo. |
| RS-03 | El cuerpo del correo nunca se persiste: ni en la base, ni en logs, ni en la cola. |
| RS-04 | Antes de llegar a la IA, el texto pasa por la detección de datos personales (Presidio, español e inglés, cédula/NIT). |
| RS-05 | Cada correo es entrada no confiable: va delimitado en el prompt, se procesa un correo por llamada, la salida se valida contra un esquema y el modelo no tiene herramientas. |
| RS-06 | Export y borrado cumplen la Ley 1581 (habeas data) y el GDPR (RF-09). |
| RS-07 | Modelo de amenazas STRIDE y checklist OWASP ASVS nivel 2. |
| RS-08 | Ningún secreto en el repo: gitleaks en pre-commit y en CI. |
| RS-09 | La PWA marca los correos que fallan SPF, DKIM o DMARC (STRIDE S-03). |
| RS-10 | El push solo dice "Tu resumen está listo", sin asuntos ni remitentes (STRIDE I-06). |
| RS-11 | Tabla de auditoría de solo inserción para eventos de seguridad, sin contenido de correos (STRIDE R-01). |
| RS-12 | Si un token vence o es revocado, la cuenta queda como "requiere reconexión" y se avisa por push (STRIDE D-04). |

Trazabilidad completa en el [modelo de amenazas](03-stride.md).

## 5. Métricas de éxito

Se miden con un set de evaluación de correos **sintéticos** etiquetados a mano: al menos 200 correos, al menos 30 por categoría, mitad en español y mitad en inglés. Incluye correos con prompt injection.

| Métrica | Meta |
|---|---|
| Recall de **trabajo** | ≥ 0,95 |
| Recall de **finanzas y trámites** | ≥ 0,95 |
| Precisión de **spam** (no esconder correos legítimos) | ≥ 0,95 |
| F1 macro (5 categorías) | ≥ 0,85 |
| Correos de inyección que cambian la categoría o filtran instrucciones | 0 |
| Datos personales sintéticos que llegan al prompt | 0 |
| Tiempo de proceso por correo (GPU local) | < 30 s |

Prioridad: perder un correo de trabajo es peor que tener ruido en la categoría trabajo.

## 6. Supuestos y riesgos

- Con la app de Google en modo "Testing", el refresh token vence cada ~7 días y hay que reconectar (por verificar).
- Un modelo local de 7–9B puede no llegar a las metas. En ese caso las metas se revisan, o se habilita Claude como opción paga.
- Presidio rinde peor en español que en inglés. Se mide con el set de evaluación.
- Web Push en iOS solo funciona con la PWA instalada en la pantalla de inicio.
