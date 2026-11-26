# CCap: resumen de correos

PWA que clasifica y resume el correo de Gmail y Outlook con IA local (Ollama), pensada para la privacidad: guarda solo metadatos y resúmenes, quita datos personales antes de llamar a la IA y trata cada correo como entrada no confiable.

> Estado: esqueleto del repo. Aún no hay funcionalidad.

## Documentación

- [PRD](docs/02-prd.md): qué se construye y cómo se mide
- [Modelo de amenazas STRIDE](docs/03-stride.md)
- [Stack](docs/01-stack.md) y [decisiones de arquitectura (ADR)](docs/adr/README.md)
- [CLAUDE.md](CLAUDE.md): reglas del repo y comandos
- [SECURITY.md](SECURITY.md): cómo reportar una vulnerabilidad

## Licencia

[MIT](LICENSE)

## Arranque local

Requisitos: `uv`, `pnpm`, Docker y Ollama.

```
cp .env.example .env             # y completar
docker compose up -d db
cd backend && uv sync && uv run pytest
cd frontend && pnpm install && pnpm dev
```

Hooks de pre-commit (gitleaks + ruff):

```
cd backend && uv run pre-commit install --config ../.pre-commit-config.yaml
```
