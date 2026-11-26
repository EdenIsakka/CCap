# ADR-0007: Elección del modelo local

- Estado: **Propuesto**. Se decide con los resultados del set de evaluación.
- Fecha: 2026-11-25

## Contexto

Ollama corre en una RTX 3070 con 8 GB de VRAM. Un modelo de 7 a 9 mil millones de parámetros cuantizado a Q4 cabe entero en la GPU. Los de más de 12 mil millones no caben enteros y corren lentos. Los correos llegan en español y en inglés. Las metas están en la sección 5 del PRD.

## Decisión pendiente

Comparar 2 o 3 candidatos de 7–9B de familias distintas (Qwen, Llama, Gemma), con la versión exacta fijada, sobre el mismo set de evaluación.

Para cada uno se mide:

- recall de trabajo y de finanzas, precisión de spam, F1 macro;
- correos de inyección que cambian la categoría;
- salidas que no validan contra el esquema;
- tiempo por correo.

## Criterio

Se elige el que cumpla las metas del PRD con mejor recall de trabajo. Si ninguno las cumple, se revisan las metas o el prompt antes de considerar Claude.

## Consecuencias

Cuando se decida, este ADR pasa a "Aceptado" con la tabla de resultados y el tag exacto del modelo.
