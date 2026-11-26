# ADR-0004: Polling en el MVP, push en la fase 2

- Estado: Aceptado
- Fecha: 2026-11-25

## Contexto

El resumen del MVP es diario: no necesita enterarse de un correo en el segundo en que llega. El correo esperado (fase 2) sí necesita inmediatez. Las notificaciones push de Gmail (Pub/Sub) y de Graph (webhooks) exigen una URL HTTPS pública, renovar suscripciones (unos 7 días en Gmail, menos de 3 en Graph) y, posiblemente, una cuenta de facturación en Google Cloud.

## Decisión

- **MVP:** polling cada 15 minutos con `history.list` (Gmail) y delta query (Graph). El cursor de cada cuenta se guarda en la base.
- **Fase 2:** Gmail Pub/Sub y webhooks de Graph para el correo esperado. Cada notificación dispara el mismo proceso que el polling, y el polling sigue como respaldo.

## Alternativas

| Opción | Por qué no |
|---|---|
| Push desde el MVP | Suma el túnel público, la verificación de firmas, la renovación de suscripciones y quizás la tarjeta, para un resumen que llega una vez al día |
| Un solo fetch antes del resumen | Concentra todo el trabajo de la GPU en un pico y deja el correo esperado sin base |

## Consecuencias

- El MVP no expone ningún endpoint a internet (STRIDE, sección 1).
- La latencia máxima para ver un correo es de unos 15 minutos. Es aceptable para un resumen diario.
- El polling queda como respaldo en la fase 2: si se pierde una notificación push, el polling la recupera.
