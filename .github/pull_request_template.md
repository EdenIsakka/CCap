## Qué cambia

<!-- Una o dos líneas. Requisito que cubre: RF-xx / RS-xx. -->

## Definition of Done

- [ ] Parte de un requisito del [PRD](../docs/02-prd.md) y el título sigue los commits convencionales
- [ ] Hay un test que falló antes del cambio y ahora pasa (TDD, estructura AAA)
- [ ] El CI está en verde: ruff, mypy, pytest, eslint, tsc, vitest y gitleaks
- [ ] Ningún cuerpo de correo se persiste en la base, los logs, los argumentos de tareas ni los fixtures (RS-03)
- [ ] Los datos de prueba son sintéticos y no hay secretos (las variables nuevas van a `.env.example` sin valor)
- [ ] Las consultas nuevas se filtran por el `user_id` de la sesión (STRIDE E-03)
- [ ] No se agregan permisos OAuth de escritura (RS-01)
- [ ] Si afecta una amenaza, `docs/03-stride.md` está actualizado en este PR
- [ ] Si cambia una decisión de arquitectura, hay un ADR nuevo
- [ ] Las dependencias nuevas están justificadas abajo

## Dependencias nuevas

<!-- Cuál y por qué no bastaban unas líneas de código. Borra la sección si no hay. -->
