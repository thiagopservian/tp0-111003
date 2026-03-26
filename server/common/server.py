import socket
import logging
from common.utils import Bet, store_bets, load_bets, has_won
from common.protocol import recv_message, send_message


class Server:
    def __init__(self, port, listen_backlog, expected_agencies):
        self._running = True
        self._current_client_socket = None
        self._expected_agencies = expected_agencies
        self._finished_agencies = set()
        self._draw_done = False
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)

    def shutdown(self):
        self._running = False
        self.__close_socket(self._current_client_socket, "client")
        self._current_client_socket = None
        self.__close_socket(self._server_socket, "server")

    def run(self):
        """
        Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client communication
        finishes, server starts to accept new connections again
        """

        while self._running:
            try:
                client_sock = self.__accept_new_connection()
            except OSError:
                if not self._running:
                    break
                continue

            self.__handle_client_connection(client_sock)

    def __handle_client_connection(self, client_sock):
        self._current_client_socket = client_sock
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
            self._current_client_socket = None

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

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

        store_bets(bets)
        logging.info(f'action: apuesta_recibida | result: success | cantidad: {batch_count}')
        self.__send_response(client_sock, b"OK")

    def __handle_finish(self, client_sock, lines):
        if len(lines) < 2:
            self.__send_response(client_sock, b"ERROR")
            return

        self._finished_agencies.add(lines[1])

        if not self._draw_done and len(self._finished_agencies) >= self._expected_agencies:
            self._draw_done = True
            logging.info('action: sorteo | result: success')

        self.__send_response(client_sock, b"OK")

    def __handle_winners(self, client_sock, lines):
        if len(lines) < 2:
            self.__send_response(client_sock, b"ERROR")
            return

        if not self._draw_done:
            self.__send_response(client_sock, b"PENDING")
            return

        agency_id = int(lines[1])
        winners = []
        try:
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
