# TP0 – Ejercicio 7

Branch actual: ej7. Objetivo: cerrar el envío de apuestas por agencia, esperar el sorteo global y consultar ganadores por agencia.

## Cómo ejecutar

- Generar compose: `./generar-compose.sh docker-compose-dev.yaml 5`.
- Verificar datasets en `.data/agency-1.csv` ... `.data/agency-5.csv`.
- Levantar entorno: `make docker-compose-up`.
- Ver logs: `make docker-compose-logs`.
- Bajar entorno: `make docker-compose-down`.

Los clientes montan `.data` como volumen (`./.data:/data`) y cada agencia N lee `/data/agency-N.csv`.

## Protocolo de comunicación

Se mantiene framing binario (header de 4 bytes big-endian + payload) y se agregan comandos en la primera línea del payload:

- `BATCH`
- `FINISH`
- `WINNERS`

Módulos:

- Cliente: [client/common/protocol.go](client/common/protocol.go)
- Servidor: [server/common/protocol.py](server/common/protocol.py)

### Mensajes

- Batch de apuestas:
	- Línea 1: `BATCH`
	- Línea 2: cantidad de apuestas
	- Líneas siguientes: `agencia|nombre|apellido|documento|nacimiento|numero`
- Notificación de fin:
	- `FINISH\n<agency_id>`
- Consulta de ganadores:
	- `WINNERS\n<agency_id>`

### Respuestas

- `OK`
- `ERROR`
- `PENDING` cuando todavía no se completó el sorteo
- `WINNERS|<cant>|<dni1>|...`

## Lógica de negocio

- Cada cliente envía todos sus batches como en ej6.
- Al terminar envía `FINISH`.
- Luego consulta `WINNERS` en loop hasta salir de estado `PENDING`.
- Al recibir resultados registra:
	- `action: consulta_ganadores | result: success | cant_ganadores: ${CANT}`

Servidor:

- Acumula notificaciones `FINISH` por agencia.
- El número esperado de agencias se recibe por `SERVER_EXPECTED_AGENCIES` desde el compose generado.
- Cuando recibe todas las notificaciones registra:
	- `action: sorteo | result: success`
- Recién desde ese momento responde consultas de ganadores.
- Para cada consulta filtra por agencia y calcula ganadores usando `load_bets(...)` y `has_won(...)`.

No se realiza broadcast global. Cada cliente recibe solo sus DNIs ganadores.

## Manejo de short read / short write

- Cliente: `SendAll` y `RecvAll` en [client/common/protocol.go](client/common/protocol.go).
- Servidor: `send_all` y `recv_all` en [server/common/protocol.py](server/common/protocol.py).

## Tests

- En `tp0-tests`:
	- `REPO_PATH=/ruta/al/repo .venv/bin/pytest test_ej7.py -q`

