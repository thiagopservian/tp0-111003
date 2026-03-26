# TP0 – Ejercicio 5

Objetivo: implementar el caso de uso Lotería Nacional, enviando una apuesta desde cliente y almacenándola en servidor.

## Cómo correr el ejercicio

- Generar compose: `./generar-compose.sh docker-compose-dev.yaml 5`.
- Levantar entorno: `make docker-compose-up` (o `docker compose -f docker-compose-dev.yaml up -d`).
- Ver logs: `make docker-compose-logs` (o `docker compose -f docker-compose-dev.yaml logs -f`).
- Bajar entorno: `make docker-compose-down`.

### Variables de entorno de la apuesta (cliente)

Cada cliente/agencia envía una apuesta con:

- `CLI_NOMBRE`
- `CLI_APELLIDO`
- `CLI_DOCUMENTO`
- `CLI_NACIMIENTO` (formato `YYYY-MM-DD`)
- `CLI_NUMERO`

Además se usa `CLI_ID` como identificador de agencia.

## Detalles de la solución

### Modelo de comunicación / protocolo

Se implementó un módulo de protocolo en ambos lados:

- Cliente: [client/common/protocol.go](client/common/protocol.go)
- Servidor: [server/common/protocol.py](server/common/protocol.py)

Formato de mensaje:

1. Header de 4 bytes big-endian con la longitud del payload.
2. Payload en bytes con los campos serializados.

Serialización de la apuesta (cliente → servidor):

`agency\nnombre\napellido\ndocumento\nnacimiento\nnumero`

Respuesta del servidor:

- `OK` si se almacenó correctamente.
- `ERROR` si el formato es inválido.

### Manejo de short read / short write

- En cliente (`SendAll`/`RecvAll`) y servidor (`send_all`/`recv_all`) se itera hasta enviar/recibir todos los bytes esperados.
- Con esto se evita asumir que un solo `send`/`recv` transfiere el mensaje completo.

### Separación de responsabilidades

- Capa de protocolo: framing y transferencia confiable de bytes.
- Lógica de negocio cliente: construcción de apuesta y log de confirmación.
- Lógica de negocio servidor: parseo, validación básica de 6 campos, creación de `Bet` y persistencia con `store_bets(...)`.

### Logs requeridos

- Cliente, al confirmar: `action: apuesta_enviada | result: success | dni: ${DNI} | numero: ${NUMERO}`.
- Servidor, al persistir: `action: apuesta_almacenada | result: success | dni: ${DNI} | numero: ${NUMERO}`.

## Tests

- En `tp0-tests`: `REPO_PATH=/ruta/al/repo .venv/bin/pytest test_ej5.py -q`.

