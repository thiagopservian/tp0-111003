import struct


def send_all(sock, data: bytes):
    """Send all bytes to socket, avoiding short-write."""
    while data:
        sent = sock.send(data)
        data = data[sent:]


def recv_all(sock, n: int) -> bytes:
    """Receive exactly n bytes from socket, avoiding short-read."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("Connection closed while receiving data")
        buf += chunk
    return buf


def send_message(sock, payload: bytes):
    """Send a length-prefixed message: 4 bytes big-endian length + payload."""
    length = struct.pack('>I', len(payload))
    send_all(sock, length)
    send_all(sock, payload)


def recv_message(sock) -> bytes:
    """Receive a length-prefixed message: 4 bytes big-endian length + payload."""
    header = recv_all(sock, 4)
    length = struct.unpack('>I', header)[0]
    return recv_all(sock, length)
