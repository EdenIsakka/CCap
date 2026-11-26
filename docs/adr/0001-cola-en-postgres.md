# ADR-0001: Cola de tareas en Postgres (Procrastinate)

- Estado: Aceptado
- Fecha: 2026-11-25

## Contexto

El worker procesa correos fuera del ciclo de petición HTTP: polling, clasificación, resumen y envío del push diario. Todo corre en un solo PC, que también ejecuta Ollama en la GPU. Restricción: costo cero y pocos servicios que operar.

## Decisión

Usar **Procrastinate**, una cola de tareas que vive en la misma base Postgres. Incluye tareas periódicas (polling cada 15 minutos, resumen diario, purga a los 30 días) y reintentos.

## Alternativas

| Opción | Por qué no |
|---|---|
| Celery + Redis | Suma un servicio (Redis) que gasta RAM y hay que operar. Encolar no es transaccional con Postgres: puede quedar un correo guardado sin su tarea, o al revés. |
| arq / Dramatiq + Redis | El mismo problema de Redis |
| `BackgroundTasks` de FastAPI | Sin persistencia ni reintentos: si el proceso cae, la tarea se pierde |

## Consecuencias

- La tarea se encola en la misma transacción que guarda el dato.
- Hay un servicio menos en `docker compose`.
- Procrastinate es menos conocido que Celery en el mercado. Se compensa explicando esta decisión.
- Con mucho volumen, Postgres como cola tendría límites. Para una sola persona no aplica.
- Los argumentos de las tareas solo llevan IDs, nunca contenido de correos (STRIDE I-02).
