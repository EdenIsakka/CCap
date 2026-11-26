# CCap: resumen de correos (PWA)

PWA que clasifica y resume el correo de Gmail y Outlook. Una persona usuaria, todo local, costo cero.
Antes de cambiar algo, lee el documento que lo gobierna:

- Qué se construye: [docs/02-prd.md](docs/02-prd.md) (requisitos RF-xx y RS-xx)
- Amenazas y mitigaciones: [docs/03-stride.md](docs/03-stride.md)
- Por qué el stack es así: [docs/01-stack.md](docs/01-stack.md) y [docs/adr/](docs/adr/README.md)

## Estructura

- `backend/`: FastAPI + Procrastinate + SQLAlchemy async. Proyecto `uv`.
- `frontend/`: PWA en TypeScript (Vite + React). Proyecto `pnpm`.
- `docs/`: PRD, STRIDE y ADR.

## Comandos

Backend (desde `backend/`):

```
uv sync
uv run ruff check . && uv run ruff format --check .
uv run mypy
uv run pytest
uv run uvicorn ccap.main:app --reload
```

Frontend (desde `frontend/`):

```
pnpm install
pnpm lint && pnpm typecheck && pnpm test
pnpm dev
```

Base de datos: `docker compose up -d db` desde la raíz.

## Reglas no negociables (seguridad y datos)

1. **El cuerpo de un correo nunca se persiste**: ni en la base, ni en logs, ni en argumentos de tareas, ni en fixtures con datos reales (RS-03). La cola transporta IDs.
2. **Todo texto de correo es entrada no confiable.** Va a la IA solo después de quitarle los datos personales (RS-04), un correo por llamada, entre delimitadores, sin herramientas, con la salida validada contra un esquema (ADR-0006).
3. **Permisos OAuth de solo lectura.** No agregues permisos de escritura sin un ADR (RS-01).
4. **Tokens OAuth siempre cifrados** con el módulo de cifrado (ADR-0005). Nunca en logs.
5. **Toda consulta a la base se filtra por el `user_id` de la sesión** (STRIDE E-03).
6. **Ningún secreto en el repo.** Las variables nuevas van a `.env.example` sin valor real.
7. **Datos de prueba sintéticos.** Nunca correos reales en tests, fixtures ni en el set de evaluación.
8. Si un cambio afecta una amenaza de `docs/03-stride.md`, actualiza el documento en el mismo PR.

## Principios de diseño

### KISS / YAGNI

No construyas lo que todavía no se necesita. Una función simple vale más que una "fábrica de fábricas".

- Nada de código "por si acaso": ni opciones, ni capas, ni configuraciones que ningún requisito RF/RS pide hoy.
- Empieza con una función. Pasa a una clase solo cuando haya estado que guardar o una interfaz que implementar.
- Tres líneas repetidas son mejores que una abstracción prematura. Abstrae a la tercera repetición, no a la primera.

### SOLID / puertos y adaptadores

Los sistemas externos se esconden detrás de una interfaz (puerto, un `typing.Protocol`). El resto del código depende de la interfaz, nunca del adaptador concreto.

```python
class EmailProvider(Protocol):
    async def fetch_new(self, cursor: str | None) -> tuple[list[MessageRef], str]: ...
    async def get_message(self, ref: MessageRef) -> RawMessage: ...
```

- `GmailAdapter` y `OutlookAdapter` implementan `EmailProvider`. El poller y el worker no saben cuál usan, por eso agregar Outlook no rompe nada.
- `fetch_new` devuelve solo referencias (ID + metadatos), nunca cuerpos: eso es lo que viaja por la cola (RS-03). El worker pide el cuerpo con `get_message` y lo descarta al terminar.
- Igual con la IA: `LLMClient`, implementado por `OllamaClient` y `ClaudeClient` (ADR-0003).
- **Puertos solo en las fronteras externas** (correo, IA, push, reloj si hace falta en tests). La lógica interna no lleva interfaces: eso sería YAGNI.
- Los adaptadores se eligen en un solo lugar (la composición de la app), no con `if provider == ...` repartidos por el código.

### Tests AAA

Cada test tiene tres partes: **Arrange** (preparar), **Act** (ejecutar una sola acción), **Assert** (verificar).

```python
def test_marca_como_spam_correo_con_phishing():
    correo = crear_correo(asunto="Gana $1000 ya")   # Arrange
    resultado = clasificar(correo)                  # Act
    assert resultado.categoria == "spam"            # Assert
```

- Un comportamiento por test. El nombre del test dice qué comportamiento verifica.
- **Unit tests vs. set de evaluación.** Los unit tests prueban la lógica con el `LLMClient` reemplazado por un fake (`clasificar(correo, llm=FakeLLM(...))`): son rápidos, deterministas y corren en CI. Si el modelo *acierta* (¿"Gana $1000 ya" es spam?) no se prueba en unit tests: se mide en el set de evaluación contra el modelo real, que corre aparte y no bloquea el CI.
- En los tests, los puertos se reemplazan con fakes simples escritos a mano. Para HTTP se usa `respx`, no mocks del adaptador.
- Los datos de prueba son sintéticos (ver regla 7).

## Forma de trabajo

- **Spec primero, luego TDD**: cada funcionalidad parte de un requisito RF/RS. Primero el test que falla, después el código.
- **PRs pequeños**: un requisito o una pieza por PR.
- **GitHub Flow** (regla):
  1. `main` siempre funciona. Nunca se hace push directo: está protegida.
  2. Cada cambio sale de `main` en una rama corta con el tipo del commit y lo que hace: `feat/rf-04-clasificar-correo`, `fix/token-refresh`, `docs/adr-0008`.
  3. Abre el PR temprano y completa la checklist de la [plantilla de PR](.github/pull_request_template.md).
  4. Se fusiona a `main` solo con el CI en verde (`backend`, `frontend`, `gitleaks`) y la rama al día con `main`.
  5. Al fusionar, la rama se borra. No hay ramas `develop` ni `release`.
- **Commits convencionales**: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`, `ci:`. Mencionar el requisito cuando aplique (`feat(worker): clasificar correo nuevo (RF-04)`).
- **Decisión de arquitectura nueva o cambiada = ADR nuevo** en `docs/adr/`. Un ADR aceptado no se edita: se reemplaza.
- El código y los nombres van en inglés. Docs, ADR y mensajes al usuario van en español.
- `mypy --strict` y `tsc --strict` sin `# type: ignore` ni `any` sin justificar en un comentario.
- No agregues dependencias por unas pocas líneas de código. Si agregas una, justifícala en el PR.
