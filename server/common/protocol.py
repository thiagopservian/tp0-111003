import struct


def send_all(sock, data: bytes):
    while data:
        sent = sock.send(data)
        data = data[sent:]


def recv_all(sock, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed while receiving data")
        buf += chunk
    return buf


def send_message(sock, payload: bytes):
    length = struct.pack('>I', len(payload))
    send_all(sock, length)
    send_all(sock, payload)


def recv_message(sock) -> bytes:
    header = recv_all(sock, 4)
    length = struct.unpack('>I', header)[0]
    return recv_all(sock, length)
