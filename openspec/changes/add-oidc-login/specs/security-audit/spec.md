# Spec Delta

## Purpose

Registro de solo inserción de los eventos de seguridad, para poder demostrar qué pasó y cuándo (habeas data, STRIDE R-01), sin guardar contenido de correos ni secretos.

## ADDED Requirements

### Requirement: Eventos de sesión en la auditoría
El sistema SHALL registrar en la auditoría cada login exitoso, cada login rechazado y cada logout, con la fecha y hora, el tipo de evento, el proveedor y el usuario cuando se conoce.

#### Scenario: Login exitoso
- **WHEN** una persona permitida inicia sesión
- **THEN** la auditoría tiene un evento de login exitoso con el proveedor, el usuario y la hora

#### Scenario: Login rechazado
- **WHEN** se rechaza un login porque el correo no está permitido
- **THEN** la auditoría tiene un evento de login rechazado con el proveedor, la hora y el motivo

#### Scenario: Logout
- **WHEN** la persona usuaria cierra sesión
- **THEN** la auditoría tiene un evento de logout con el usuario y la hora

### Requirement: Sin datos sensibles en la auditoría
La auditoría MUST NOT guardar tokens, identificadores de sesión, contenido de correos ni la dirección de correo de un login rechazado.

#### Scenario: Login rechazado sin correo
- **WHEN** se registra un login rechazado
- **THEN** el evento no contiene la dirección de correo ni el ID token

### Requirement: Solo inserción
La base de datos MUST impedir que se modifiquen o borren eventos de la auditoría.

#### Scenario: Intento de modificar
- **WHEN** se intenta actualizar un evento existente de la auditoría
- **THEN** la base de datos rechaza la operación y el evento queda igual

#### Scenario: Intento de borrar
- **WHEN** se intenta borrar un evento de la auditoría
- **THEN** la base de datos rechaza la operación y el evento sigue ahí
