# TP0 – Ejercicio 2

Branch actual: ej2. Objetivo: que cliente y servidor lean configuración montada como volumen, evitando reconstruir imágenes al cambiar parámetros.

## Cómo correr el ejercicio

- Generar el compose con la cantidad deseada de clientes: `./generar-compose.sh docker-compose-dev.yaml <cantidad_de_clientes>`.
- Ajustar configuración antes de levantar:
	- Cliente: [client/config.yaml](client/config.yaml) (loop_amount, loop_period, log.level, server.address).
	- Servidor: [server/config.ini](server/config.ini) (port, listen_backlog, logging_level).
- Construir imágenes **solo si cambiaste código** (los cambios de config no requieren rebuild): `make docker-image` o `docker build -f ./server/Dockerfile -t server:latest .` y `docker build -f ./client/Dockerfile -t client:latest .`.
- Levantar entorno: `make docker-compose-up` o `docker compose -f docker-compose-dev.yaml up -d`.
- Ver logs: `make docker-compose-logs` (usa `grep` para filtrar) o `docker compose -f docker-compose-dev.yaml logs -f`.
- Bajar entorno: `make docker-compose-down`.

## Detalles de la solución

- Los archivos de config se montan como volúmenes en los contenedores; cambiar parámetros y volver a levantar es suficiente, sin rebuild de imágenes.
- El cliente usa viper: prioriza variables de entorno `CLI_*` sobre valores de [client/config.yaml](client/config.yaml).
- El servidor usa ConfigParser: prioriza variables de entorno (`SERVER_PORT`, `SERVER_LISTEN_BACKLOG`, `LOGGING_LEVEL`) sobre [server/config.ini](server/config.ini).

## Tests

- En `tp0-tests`, ejecutar `REPO_PATH=/ruta/al/repo .venv/bin/pytest test_ej2.py -q` o `make test` desde esa carpeta. Asegúrate de tener docker accesible sin sudo.

