# TP0 – Ejercicio 8

Branch actual: ej8. Objetivo: permitir aceptación y procesamiento en paralelo en servidor, manteniendo consistencia de persistencia y estado de sorteo.

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

## Concurrencia y sincronización

- El servidor acepta conexiones en el hilo principal y procesa cada cliente en un thread independiente.
- Se usa un lock de persistencia para serializar acceso a `store_bets(...)` y `load_bets(...)`.
- Se usa un lock de sockets activos para cerrar conexiones de forma ordenada durante shutdown.
- Se usa `Condition` sobre el estado del sorteo para coordinar:
	- notificaciones `FINISH`,
	- transición a sorteo completado,
	- consultas de ganadores que deben esperar hasta tener sorteo habilitado.

## Manejo de short read / short write

- Cliente: `SendAll` y `RecvAll` en [client/common/protocol.go](client/common/protocol.go).
- Servidor: `send_all` y `recv_all` en [server/common/protocol.py](server/common/protocol.py).

## Tests

- En `tp0-tests`:
	- `REPO_PATH=/ruta/al/repo .venv/bin/pytest test_ej8.py -q`

