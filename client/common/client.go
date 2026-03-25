package common

import (
	"bufio"
	"context"
	"fmt"
	"net"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	LoopAmount    int
	LoopPeriod    time.Duration
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

// CreateClientSocket Initializes client socket. In case of
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

// StartClientLoop Send messages to the client until some time threshold is met
func (c *Client) StartClientLoop(ctx context.Context) {
	// There is an autoincremental msgID to identify every message sent
	// Messages if the message amount threshold has not been surpassed
	for msgID := 1; msgID <= c.config.LoopAmount; msgID++ {
		select {
		case <-ctx.Done():
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			c.closeClientSocket()
			return
		default:
		}

		// Create the connection the server in every loop iteration. Send an
		if err := c.createClientSocket(); err != nil {
			return
		}

		// TODO: Modify the send to avoid short-write
		_, err := fmt.Fprintf(
			c.conn,
			"[CLIENT %v] Message N°%v\n",
			c.config.ID,
			msgID,
		)
		if err != nil {
			if ctx.Err() != nil {
				log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
				c.closeClientSocket()
				return
			}

			log.Errorf("action: send_message | result: fail | client_id: %v | error: %v", c.config.ID, err)
			c.closeClientSocket()
			return
		}

		msg, err := bufio.NewReader(c.conn).ReadString('\n')
		c.closeClientSocket()

		if err != nil {
			if ctx.Err() != nil {
				log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
				return
			}

			log.Errorf("action: receive_message | result: fail | client_id: %v | error: %v",
				c.config.ID,
				err,
			)
			return
		}

		log.Infof("action: receive_message | result: success | client_id: %v | msg: %v",
			c.config.ID,
			msg,
		)

		// Wait a time between sending one message and the next one
		select {
		case <-ctx.Done():
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			return
		case <-time.After(c.config.LoopPeriod):
		}

	}
	log.Infof("action: loop_finished | result: success | client_id: %v", c.config.ID)
}
