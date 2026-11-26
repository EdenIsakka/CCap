# ADR-0003: Ollama por defecto, Claude opcional

- Estado: Aceptado
- Fecha: 2026-11-25

## Contexto

La IA clasifica y resume cada correo. El proyecto debe costar cero y procesa contenido sensible. El PC tiene una RTX 3070 con 8 GB de VRAM. El enunciado pide que los proveedores de IA sean intercambiables.

## Decisión

- Un `Protocol` `LLMClient` con un método que recibe el texto sin datos personales y devuelve un modelo Pydantic `Clasificacion` (`categoria: Categoria`, `resumen: str`).
- **`OllamaClient`** es el proveedor por defecto. Usa salida estructurada con JSON Schema.
- **`ClaudeClient`** usa el SDK oficial `anthropic` con structured outputs. Se activa con `LLM_PROVIDER=claude` y `ANTHROPIC_API_KEY`. El modelo es configurable, con `claude-opus-5-5` por defecto.
- Las dos implementaciones pasan el mismo set de evaluación.

## Alternativas

| Opción | Por qué no |
|---|---|
| Solo Claude | Cuesta dinero y saca los datos del PC |
| Solo Ollama | Pierde la intercambiabilidad que pide el enunciado y la comparación de calidad |
| LiteLLM u otra capa genérica | Una dependencia grande para dos proveedores |

## Consecuencias

- Con la configuración por defecto, ningún contenido sale del PC.
- En CI, `ClaudeClient` se prueba solo con mocks. No se gasta dinero.
- La calidad depende del modelo local elegido (ADR-0007).
- Activar Claude implica revisar el modelo de amenazas: Presidio pasa a ser el único control antes de que el texto salga del PC (STRIDE I-03).
