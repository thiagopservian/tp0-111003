# TP0 – Ejercicio 6

Branch actual: ej6. Objetivo: enviar apuestas por lotes (batchs) desde archivos por agencia y procesarlas en servidor por batch.

## Cómo ejecutar

- Generar compose: `./generar-compose.sh docker-compose-dev.yaml 5`.
- Verificar datasets en `.data/agency-1.csv` ... `.data/agency-5.csv`.
- Levantar entorno: `make docker-compose-up`.
- Ver logs: `make docker-compose-logs`.
- Bajar entorno: `make docker-compose-down`.

Los clientes montan `.data` como volumen (`./.data:/data`) y cada agencia N lee `/data/agency-N.csv`.

## Protocolo de comunicación implementado

- Framing de transporte (cliente y servidor):
	1. Header de 4 bytes (`uint32` big-endian) con largo del payload.
	2. Payload con serialización manual.
- Módulos:
	- Cliente: [client/common/protocol.go](client/common/protocol.go)
	- Servidor: [server/common/protocol.py](server/common/protocol.py)

### Serialización del batch

- Línea 1: cantidad de apuestas del batch.
- Líneas siguientes: una apuesta por línea con formato:

`agencia|nombre|apellido|documento|nacimiento|numero`

## Lógica de batch

- `batch.maxAmount` en [client/config.yaml](client/config.yaml) define el tamaño máximo por batch.
- Valor por defecto: `64` (manteniendo paquetes por debajo de ~8kB en este escenario).
- El cliente divide el archivo de la agencia en chunks de tamaño `batch.maxAmount` y envía cada chunk en una conexión.
- El servidor valida que el batch esté bien formado y que todas las apuestas sean parseables.

## Respuesta y logs

- Si todo el batch se procesa correctamente:
	- respuesta: `OK`
	- log servidor: `action: apuesta_recibida | result: success | cantidad: N`
- Si hay error en alguna apuesta del batch:
	- respuesta: `ERROR`
	- log servidor: `action: apuesta_recibida | result: fail | cantidad: N`

## Manejo de short read / short write

- Cliente: `SendAll` y `RecvAll` en [client/common/protocol.go](client/common/protocol.go).
- Servidor: `send_all` y `recv_all` en [server/common/protocol.py](server/common/protocol.py).
- Ambos buclean hasta transferir exactamente la cantidad esperada de bytes.

## Tests

- En `tp0-tests`:
	- `REPO_PATH=/ruta/al/repo .venv/bin/pytest test_ej6.py -q`

