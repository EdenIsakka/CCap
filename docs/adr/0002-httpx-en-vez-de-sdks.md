# ADR-0002: `httpx` directo en vez de los SDKs de Google y Microsoft

- Estado: Aceptado. La librería (`httpx`) fue reemplazada por `httpx2` en [ADR-0009](0009-httpx2-en-vez-de-httpx.md)
- Fecha: 2026-11-25

## Contexto

Hacen falta dos adaptadores, Gmail y Microsoft Graph, detrás de una interfaz común (`EmailProvider`). La app es async (FastAPI, SQLAlchemy async). Solo se usan unas pocas operaciones de solo lectura: listar cambios, leer un mensaje y renovar el token.

## Decisión

Llamar a las APIs REST con **`httpx.AsyncClient`**, y usar **`authlib`** para OAuth. Cada adaptador implementa un `Protocol` `EmailProvider` con este contrato mínimo:

- `fetch_new(cursor) -> (refs, nuevo_cursor)`: referencias (ID + metadatos), nunca cuerpos
- `get_message(ref) -> RawMessage`
- `web_link(ref) -> str`

## Alternativas

| Opción | Por qué no |
|---|---|
| `google-api-python-client` | Síncrono, pesado y con descubrimiento dinámico de la API, que mypy no puede tipar |
| `msgraph-sdk` | Muchas dependencias para usar tres endpoints |

## Consecuencias

- Los adaptadores son delgados, tipados y se testean con `respx` sin red.
- Paginación, reintentos con `Retry-After` y renovación de tokens se escriben a mano. Son pocas líneas, pero hay que testearlas.
- Si Google o Microsoft cambian la API, no hay un SDK que absorba el cambio. El riesgo es bajo: son APIs versionadas (`gmail/v1`, Graph `v1.0`).
