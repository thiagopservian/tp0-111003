import socket
import logging
import threading
from common.utils import Bet, store_bets, load_bets, has_won
from common.protocol import recv_message, send_message


class Server:
    def __init__(self, port, listen_backlog, expected_agencies):
        self._running = True
        self._expected_agencies = expected_agencies
        self._finished_agencies = set()
        self._draw_done = False
        self._state_lock = threading.Lock()
        self._draw_condition = threading.Condition(self._state_lock)
        self._storage_lock = threading.Lock()
        self._clients_lock = threading.Lock()
        self._client_sockets = set()
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

    def shutdown(self):
        with self._draw_condition:
            self._running = False
            self._draw_condition.notify_all()

        self.__close_socket(self._server_socket, "server")

        with self._clients_lock:
            sockets = list(self._client_sockets)

        for sock in sockets:
            self.__close_socket(sock, "client")

    def run(self):
        while self._running:
            try:
                client_sock = self.__accept_new_connection()
            except OSError:
                if not self._running:
                    break
                continue

            worker = threading.Thread(target=self.__handle_client_connection, args=(client_sock,), daemon=True)
            worker.start()

    def __handle_client_connection(self, client_sock):
        with self._clients_lock:
            self._client_sockets.add(client_sock)

        try:
            data = recv_message(client_sock).decode('utf-8')
            lines = data.split('\n')
            command = lines[0]

            if command == 'BATCH':
                self.__handle_batch(client_sock, lines)
            elif command == 'FINISH':
                self.__handle_finish(client_sock, lines)
            elif command == 'WINNERS':
                self.__handle_winners(client_sock, lines)
            else:
                self.__send_response(client_sock, b"ERROR")

        except (OSError, ConnectionError) as e:
            if self._running:
                logging.error(f"action: apuesta_recibida | result: fail | cantidad: 0 | error: {e}")
                self.__send_response(client_sock, b"ERROR")
        except Exception:
            logging.info('action: apuesta_recibida | result: fail | cantidad: 0')
            self.__send_response(client_sock, b"ERROR")
        finally:
            self.__close_socket(client_sock, "client")
            with self._clients_lock:
                self._client_sockets.discard(client_sock)

    def __accept_new_connection(self):
        logging.info('action: accept_connections | result: in_progress')
        c, addr = self._server_socket.accept()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def __handle_batch(self, client_sock, lines):
        if len(lines) < 2:
            logging.info('action: apuesta_recibida | result: fail | cantidad: 0')
            self.__send_response(client_sock, b"ERROR")
            return

        batch_count = int(lines[1])
        bet_lines = lines[2:]

        if len(bet_lines) != batch_count:
            logging.info(f'action: apuesta_recibida | result: fail | cantidad: {len(bet_lines)}')
            self.__send_response(client_sock, b"ERROR")
            return

        bets = []
        for line in bet_lines:
            fields = line.split('|')
            if len(fields) != 6:
                logging.info(f'action: apuesta_recibida | result: fail | cantidad: {batch_count}')
                self.__send_response(client_sock, b"ERROR")
                return

            agency, first_name, last_name, document, birthdate, number = fields
            bets.append(Bet(agency=agency, first_name=first_name, last_name=last_name, document=document, birthdate=birthdate, number=number))

        with self._storage_lock:
            store_bets(bets)
        logging.info(f'action: apuesta_recibida | result: success | cantidad: {batch_count}')
        self.__send_response(client_sock, b"OK")

    def __handle_finish(self, client_sock, lines):
        if len(lines) < 2:
            self.__send_response(client_sock, b"ERROR")
            return

        with self._draw_condition:
            self._finished_agencies.add(lines[1])

            if not self._draw_done and len(self._finished_agencies) >= self._expected_agencies:
                self._draw_done = True
                logging.info('action: sorteo | result: success')

            self._draw_condition.notify_all()

        self.__send_response(client_sock, b"OK")

    def __handle_winners(self, client_sock, lines):
        if len(lines) < 2:
            self.__send_response(client_sock, b"ERROR")
            return

        with self._draw_condition:
            while self._running and not self._draw_done:
                self._draw_condition.wait(timeout=0.2)

            if not self._draw_done:
                self.__send_response(client_sock, b"PENDING")
                return

        agency_id = int(lines[1])
        winners = []
        try:
            with self._storage_lock:
                for bet in load_bets():
                    if bet.agency == agency_id and has_won(bet):
                        winners.append(str(bet.document))
        except FileNotFoundError:
            winners = []

        payload = 'WINNERS|' + str(len(winners))
        if winners:
            payload += '|' + '|'.join(winners)
        self.__send_response(client_sock, payload.encode('utf-8'))

    def __close_socket(self, sock, socket_name):
        if sock is None:
            return

        try:
            sock.close()
            logging.info(f'action: close_socket | result: success | socket: {socket_name}')
        except OSError as e:
            logging.error(f'action: close_socket | result: fail | socket: {socket_name} | error: {e}')

    def __send_response(self, sock, payload):
        try:
            send_message(sock, payload)
        except OSError:
            pass
