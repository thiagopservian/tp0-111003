# TP0 – Ejercicio 1

ej1. Objetivo: generar dinámicamente el archivo Docker Compose con una cantidad configurable de clientes.

## Cómo correr el ejercicio

- Generar el compose con la cantidad deseada de clientes: `./generar-compose.sh docker-compose-dev.yaml <cantidad_de_clientes>`.
- Construir imágenes: `make docker-image` o `docker build -f ./server/Dockerfile -t server:latest .` y `docker build -f ./client/Dockerfile -t client:latest .`.
- Levantar entorno: `make docker-compose-up` o `docker compose -f docker-compose-dev.yaml up -d`.
- Ver logs: `make docker-compose-logs` (usa `grep` para filtrar) o `docker compose -f docker-compose-dev.yaml logs -f`.
- Bajar entorno: `make docker-compose-down`.

## Detalles de la solución

- El script `generar-compose.sh` recibe como parámetros el nombre del archivo de salida y la cantidad de clientes, y delega la generación en `generar-compose.py`.
- `generar-compose.py` construye el YAML de Docker Compose programáticamente: define el servicio `server` (único), N servicios `clientX` (cada uno con `CLI_ID=X` y `depends_on: server`) y la red `testing_net` con subnet fija.
- Los nombres de los contenedores siguen el formato `client1`, `client2`, …, `clientN` según lo requerido por el enunciado.

## Tests

- En `tp0-tests`, ejecutar `REPO_PATH=/ruta/al/repo .venv/bin/pytest test_ej1.py -q` o `make test` desde esa carpeta. Asegúrate de tener docker accesible sin sudo.
