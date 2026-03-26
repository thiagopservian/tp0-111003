import socket
import logging
from common.utils import Bet, store_bets
from common.protocol import recv_message, send_message


class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._running = True
        self._current_client_socket = None
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
            data = recv_message(client_sock)
            fields = data.decode('utf-8').split('\n')

            if len(fields) != 6:
                logging.error(f'action: receive_bet | result: fail | error: expected 6 fields, got {len(fields)}')
                send_message(client_sock, b"ERROR")
                return

            agency, first_name, last_name, document, birthdate, number = fields

            bet = Bet(
                agency=agency,
                first_name=first_name,
                last_name=last_name,
                document=document,
                birthdate=birthdate,
                number=number
            )
            store_bets([bet])

            logging.info(f'action: apuesta_almacenada | result: success | dni: {document} | numero: {number}')

            send_message(client_sock, b"OK")

        except (OSError, ConnectionError) as e:
            if self._running:
                logging.error(f"action: receive_bet | result: fail | error: {e}")
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

    def __close_socket(self, sock, socket_name):
        if sock is None:
            return

        try:
            sock.close()
            logging.info(f'action: close_socket | result: success | socket: {socket_name}')
        except OSError as e:
            logging.error(f'action: close_socket | result: fail | socket: {socket_name} | error: {e}')
