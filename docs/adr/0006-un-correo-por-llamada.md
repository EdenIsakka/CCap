# ADR-0006: Un correo por llamada a la IA

- Estado: Aceptado
- Fecha: 2026-11-25

## Contexto

Cada correo es entrada no confiable y puede contener prompt injection (STRIDE T-01, I-08). El resumen del MVP es una línea por correo.

## Decisión

Cada llamada a la IA procesa **un solo correo**, con estas reglas:

- Las instrucciones van en el prompt de sistema. El correo va en el mensaje de usuario, entre delimitadores, marcado como dato a analizar y no como instrucciones.
- El texto llega sin datos personales y truncado a un largo máximo.
- El modelo no tiene herramientas.
- La salida se valida contra el esquema `Clasificacion`. La categoría es un `enum` y el resumen tiene largo máximo. Si la salida no es válida tras un reintento, el correo va a "otros" y se marca para revisión.

## Alternativas

| Opción | Por qué no |
|---|---|
| Varios correos por llamada | Más barato y rápido, pero un correo malicioso puede alterar la clasificación de los demás o filtrar su contenido |
| Un resumen por categoría redactado por la IA | Mezcla correos no confiables en un mismo contexto. Fue descartado en el PRD. |

## Consecuencias

- Una inyección exitosa solo afecta a su propio correo.
- Hay más llamadas. Con Ollama local el costo es solo tiempo de GPU, aceptable para el volumen de una persona.
- El set de evaluación mide cada correo por separado: la métrica es directa.
- El contenido de un correo nunca va en el prompt de sistema.
