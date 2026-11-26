# ADR-0005: Cifrado de tokens OAuth con AES-GCM

- Estado: Aceptado
- Fecha: 2026-11-25

## Contexto

Los refresh tokens dan lectura de todo el buzón. Si alguien obtiene una copia de la base (un backup, un volumen de Docker), no debe poder usarlos (STRIDE I-01).

## Decisión

- **AES-256-GCM** con `cryptography` (`AESGCM`), un nonce aleatorio de 96 bits por cifrado.
- **AAD** = `user_id` + `account_id`. Un token copiado a otra fila no se descifra.
- La llave viene de la variable de entorno `TOKEN_ENCRYPTION_KEYS`, nunca de la base ni del repo.
- Cada fila guarda `key_version`. Para rotar: se agrega una llave nueva, se re-cifra en segundo plano y se retira la vieja.

## Alternativas

| Opción | Por qué no |
|---|---|
| `pgcrypto` en Postgres | La llave viaja en las consultas SQL y puede terminar en los logs de Postgres |
| Fernet | Más simple, pero no tiene AAD y rotar llaves exige `MultiFernet`. AES-GCM con versión de llave es igual de corto. |
| KMS en la nube | Contradice el costo cero. Queda como opción si algún día se despliega. |

## Consecuencias

- Una copia de la base sola no sirve. Hace falta además la llave del `.env`.
- Si la llave se pierde, las cuentas se reconectan con OAuth. No se pierden datos de correo, solo los tokens.
- Un atacante con control del PC lee la llave. Es un riesgo aceptado en el modelo de amenazas.
- Se necesita un test de ida y vuelta y otro que confirme que el descifrado falla si cambia el AAD.
