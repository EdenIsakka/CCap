# ADR-0009: `httpx2` en vez de `httpx`

- Estado: Aceptado
- Fecha: 2026-11-26
- Reemplaza la elección de librería de [ADR-0002](0002-httpx-en-vez-de-sdks.md). La decisión de fondo de ese ADR (cliente HTTP directo en vez de los SDKs) sigue en pie.

## Contexto

ADR-0002 eligió `httpx`. Desde entonces, las dos librerías de las que depende el backend pasaron a `httpx2`, un fork de `httpx` con la misma API:

- Starlette avisa que su `TestClient` deja `httpx` y usa `httpx2`.
- `authlib` 1.9 usa `httpx2` para OAuth, aunque no lo declara como dependencia.

`respx`, la librería prevista para simular HTTP en los tests, solo intercepta `httpx`. Con `authlib` las peticiones salían a la red real sin que ningún test lo notara.

## Decisión

- Los adaptadores de correo y cualquier cliente HTTP propio usan **`httpx2`**, declarado como dependencia de runtime.
- En los tests, HTTP se simula con **`httpx2.MockTransport`** y un handler escrito a mano, que falla ante cualquier URL inesperada. No se usa `respx`.
- Para `authlib`, el transporte simulado se inyecta en `client_kwargs` del cliente registrado.

## Alternativas

| Opción | Por qué no |
|---|---|
| Quedarse con `httpx` | Habría dos clientes HTTP casi iguales en el proyecto, y `authlib` igual trae `httpx2` |
| `respx` | No intercepta `httpx2`: los tests de login llegaban al Google real |

## Consecuencias

- Un solo cliente HTTP en todo el backend.
- Los fakes con `MockTransport` son un poco más largos que las rutas de `respx`, pero no dependen de parchear internals.
- `httpx2` es un proyecto más nuevo. Si se abandona, la API es la de `httpx` y volver es cambiar los imports.
