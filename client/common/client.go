package common

import (
	"context"
	"net"
	"strings"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	Nombre        string
	Apellido      string
	Documento     string
	Nacimiento    string
	Numero        string
}

// Client Entity that encapsulates how
type Client struct {
	config ClientConfig
	conn   net.Conn
}

// NewClient Initializes a new client receiving the configuration
// as a parameter
func NewClient(config ClientConfig) *Client {
	client := &Client{
		config: config,
	}
	return client
}

// createClientSocket Initializes client socket. In case of
// failure, error is printed in stdout/stderr and exit 1
// is returned
func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		log.Errorf(
			"action: connect | result: fail | client_id: %v | error: %v",
			c.config.ID,
			err,
		)
		return err
	}
	c.conn = conn
	return nil
}

func (c *Client) closeClientSocket() {
	if c.conn == nil {
		return
	}

	if err := c.conn.Close(); err != nil {
		log.Errorf("action: close_socket | result: fail | client_id: %v | socket: client | error: %v", c.config.ID, err)
	} else {
		log.Infof("action: close_socket | result: success | client_id: %v | socket: client", c.config.ID)
	}

	c.conn = nil
}

func (c *Client) SendBet(ctx context.Context) {
	select {
	case <-ctx.Done():
		log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
		return
	default:
	}

	if err := c.createClientSocket(); err != nil {
		return
	}
	defer c.closeClientSocket()

	payload := strings.Join([]string{
		c.config.ID,
		c.config.Nombre,
		c.config.Apellido,
		c.config.Documento,
		c.config.Nacimiento,
		c.config.Numero,
	}, "\n")

	if err := SendMessage(c.conn, []byte(payload)); err != nil {
		if ctx.Err() != nil {
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			return
		}
		log.Errorf("action: send_bet | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	response, err := RecvMessage(c.conn)
	if err != nil {
		if ctx.Err() != nil {
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			return
		}
		log.Errorf("action: receive_confirmation | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	if string(response) == "OK" {
		log.Infof("action: apuesta_enviada | result: success | dni: %v | numero: %v",
			c.config.Documento,
			c.config.Numero,
		)
	} else {
		log.Errorf("action: apuesta_enviada | result: fail | dni: %v | numero: %v | response: %v",
			c.config.Documento,
			c.config.Numero,
			string(response),
		)
	}
}
