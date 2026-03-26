# TP0 – Ejercicio 4

Objetivo: finalizar cliente y servidor de forma graceful al recibir SIGTERM, cerrando sockets y registrando logs de cierre.

## Cómo correr el ejercicio

- Generar el compose con la cantidad deseada de clientes: `./generar-compose.sh docker-compose-dev.yaml <cantidad_de_clientes>`.
- Ajustar configuración antes de levantar:
	- Cliente: [client/config.yaml](client/config.yaml) (loop_amount, loop_period, log.level, server.address).
	- Servidor: [server/config.ini](server/config.ini) (port, listen_backlog, logging_level).
- Construir imágenes **solo si cambiaste código** (los cambios de config no requieren rebuild): `make docker-image` o `docker build -f ./server/Dockerfile -t server:latest .` y `docker build -f ./client/Dockerfile -t client:latest .`.
- Levantar entorno: `make docker-compose-up` o `docker compose -f docker-compose-dev.yaml up -d`.
- Ver logs: `make docker-compose-logs` (usa `grep` para filtrar) o `docker compose -f docker-compose-dev.yaml logs -f`.
- Probar apagado graceful:
	- Cliente: `docker stop client1 -t 20`
	- Servidor: `docker stop server -t 20`
	- Todo el sistema: `docker compose -f docker-compose-dev.yaml down -t 10`
- Bajar entorno: `make docker-compose-down`.

## Detalles de la solución

- Se usa `entrypoint` en formato exec en el compose generado para que SIGTERM llegue al proceso real (`/client` y `python3 /main.py`) y no a un shell intermedio.
- Cliente (Go): maneja SIGTERM con `signal.NotifyContext`; ante cancelación corta el loop, cierra el socket activo y loguea `action: shutdown` y `action: close_socket`.
- Servidor (Python): registra handler de SIGTERM/SIGINT; al recibir señal ejecuta `shutdown()`, cierra socket de cliente activo y socket de escucha, y sale del loop principal.
- Se agregaron logs explícitos de cierre de recursos (`close_socket`) para verificar el cierre de file descriptors durante el apagado.

## Tests

- En `tp0-tests`, ejecutar `REPO_PATH=/ruta/al/repo .venv/bin/pytest test_ej4.py -q` o `make test` desde esa carpeta. Asegúrate de tener docker accesible sin sudo.

