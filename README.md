# TP0 – Ejercicio 3

Branch actual: ej3. Objetivo: validar automáticamente el echo server con `netcat` sin exponer puertos al host.

## Cómo correr el ejercicio

- Generar el compose con la cantidad deseada de clientes: `./generar-compose.sh docker-compose-dev.yaml <cantidad_de_clientes>`.
- Ajustar configuración antes de levantar:
	- Cliente: [client/config.yaml](client/config.yaml) (loop_amount, loop_period, log.level, server.address).
	- Servidor: [server/config.ini](server/config.ini) (port, listen_backlog, logging_level).
- Construir imágenes **solo si cambiaste código** (los cambios de config no requieren rebuild): `make docker-image` o `docker build -f ./server/Dockerfile -t server:latest .` y `docker build -f ./client/Dockerfile -t client:latest .`.
- Levantar entorno: `make docker-compose-up` o `docker compose -f docker-compose-dev.yaml up -d`.
- Ver logs: `make docker-compose-logs` (usa `grep` para filtrar) o `docker compose -f docker-compose-dev.yaml logs -f`.
- Bajar entorno: `make docker-compose-down`.
- Ejecutar validación del echo server: `sh validar-echo-server.sh`.

## Detalles de la solución

- Los archivos de config se montan como volúmenes en los contenedores; cambiar parámetros y volver a levantar es suficiente, sin rebuild de imágenes.
- El cliente usa viper: prioriza variables de entorno `CLI_*` sobre valores de [client/config.yaml](client/config.yaml).
- El servidor usa ConfigParser: prioriza variables de entorno (`SERVER_PORT`, `SERVER_LISTEN_BACKLOG`, `LOGGING_LEVEL`) sobre [server/config.ini](server/config.ini).
- La validación usa `netcat` dentro de un contenedor `busybox` conectado a la red Docker del proyecto (`tp0_testing_net`), por lo que no instala herramientas en el host ni publica puertos.
- Si el mensaje recibido coincide exactamente con el enviado, el script imprime `action: test_echo_server | result: success`; en cualquier otro caso imprime `action: test_echo_server | result: fail`.

## Tests

- En `tp0-tests`, ejecutar `REPO_PATH=/ruta/al/repo .venv/bin/pytest test_ej3.py -q` o `make test` desde esa carpeta. Asegúrate de tener docker accesible sin sudo.

