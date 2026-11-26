# Política de seguridad

## Reportar una vulnerabilidad

No abras un issue público. Usa el reporte privado de GitHub: pestaña **Security** → **Report a vulnerability**.

Incluye qué componente afecta, cómo reproducirlo y el impacto que esperas. Respondo en un plazo de 7 días.

## Alcance

CCap es un proyecto personal que corre en local y no tiene una instancia pública. Aplica al código de este repositorio:

- El backend (`backend/`) y la PWA (`frontend/`)
- El manejo de tokens OAuth, el cifrado y la eliminación de datos personales
- La inyección de prompts a través del contenido de los correos

El modelo de amenazas está en [docs/03-stride.md](docs/03-stride.md).

## Versiones con soporte

Solo la rama `main`.
