#!/usr/bin/env python3
import sys

def generate_compose(output_file, client_amount):
    lines = []

    lines.append("name: tp0")
    lines.append("services:")

    # Server service
    lines.append("  server:")
    lines.append("    container_name: server")
    lines.append("    image: server:latest")
    lines.append("    entrypoint: python3 /main.py")
    lines.append("    environment:")
    lines.append("      - PYTHONUNBUFFERED=1")
    lines.append("      - LOGGING_LEVEL=DEBUG")
    lines.append("    networks:")
    lines.append("      - testing_net")

    # Client services
    for i in range(1, client_amount + 1):
        lines.append(f"")
        lines.append(f"  client{i}:")
        lines.append(f"    container_name: client{i}")
        lines.append(f"    image: client:latest")
        lines.append(f"    entrypoint: /client")
        lines.append(f"    environment:")
        lines.append(f"      - CLI_ID={i}")
        lines.append(f"      - CLI_LOG_LEVEL=DEBUG")
        lines.append(f"    networks:")
        lines.append(f"      - testing_net")
        lines.append(f"    depends_on:")
        lines.append(f"      - server")

    # Network definition
    lines.append("")
    lines.append("networks:")
    lines.append("  testing_net:")
    lines.append("    ipam:")
    lines.append("      driver: default")
    lines.append("      config:")
    lines.append("        - subnet: 172.25.125.0/24")
    lines.append("")

    with open(output_file, 'w') as f:
        f.write('\n'.join(lines))

    print(f"Archivo '{output_file}' generado con {client_amount} cliente(s).")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Uso: python3 generar-compose.py <archivo_salida> <cantidad_clientes>")
        sys.exit(1)

    output_file = sys.argv[1]
    try:
        client_amount = int(sys.argv[2])
    except ValueError:
        print(f"Error: la cantidad de clientes debe ser un número entero, se recibió '{sys.argv[2]}'")
        sys.exit(1)

    if client_amount < 1:
        print(f"Error: la cantidad de clientes debe ser mayor a 0, se recibió '{client_amount}'")
        sys.exit(1)

    generate_compose(output_file, client_amount)
