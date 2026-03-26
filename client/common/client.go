package common

import (
	"encoding/csv"
	"context"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/op/go-logging"
)

var log = logging.MustGetLogger("log")

// ClientConfig Configuration used by the client
type ClientConfig struct {
	ID            string
	ServerAddress string
	BatchMaxAmount int
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

func (c *Client) SendBatches(ctx context.Context) {
	if c.config.BatchMaxAmount <= 0 {
		c.config.BatchMaxAmount = 1
	}

	bets, err := c.loadAgencyBets()
	if err != nil {
		log.Errorf("action: load_bets | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return
	}

	for i := 0; i < len(bets); i += c.config.BatchMaxAmount {
		select {
		case <-ctx.Done():
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			return
		default:
		}

		end := i + c.config.BatchMaxAmount
		if end > len(bets) {
			end = len(bets)
		}

		batch := bets[i:end]
		if err := c.sendBatch(ctx, batch); err != nil {
			return
		}
	}

	if err := c.sendFinish(ctx); err != nil {
		return
	}

	c.queryWinners(ctx)
}

func (c *Client) sendBatch(ctx context.Context, batch [][]string) error {
	if err := c.createClientSocket(); err != nil {
		return err
	}
	defer c.closeClientSocket()

	payload := c.serializeBatchMessage(batch)
	if err := SendMessage(c.conn, []byte(payload)); err != nil {
		if ctx.Err() != nil {
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			return nil
		}
		log.Errorf("action: send_bet | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return err
	}

	response, err := RecvMessage(c.conn)
	if err != nil {
		if ctx.Err() != nil {
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			return nil
		}
		log.Errorf("action: receive_confirmation | result: fail | client_id: %v | error: %v", c.config.ID, err)
		return err
	}

	if string(response) != "OK" {
		log.Errorf("action: apuesta_enviada | result: fail | client_id: %v | cantidad: %v", c.config.ID, len(batch))
		return fmt.Errorf("batch rejected")
	}

	log.Infof("action: apuesta_enviada | result: success | client_id: %v | cantidad: %v", c.config.ID, len(batch))
	return nil
}

func (c *Client) serializeBatchMessage(batch [][]string) string {
	lines := make([]string, 0, len(batch)+1)
	lines = append(lines, "BATCH")
	lines = append(lines, strconv.Itoa(len(batch)))

	for _, row := range batch {
		lines = append(lines, strings.Join([]string{
			c.config.ID,
			row[0],
			row[1],
			row[2],
			row[3],
			row[4],
		}, "|"))
	}

	return strings.Join(lines, "\n")
}

func (c *Client) sendFinish(ctx context.Context) error {
	response, err := c.sendRequest(ctx, "FINISH\n"+c.config.ID)
	if err != nil {
		return err
	}

	if response != "OK" {
		return fmt.Errorf("finish rejected")
	}

	return nil
}

func (c *Client) queryWinners(ctx context.Context) {
	for {
		select {
		case <-ctx.Done():
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			return
		default:
		}

		response, err := c.sendRequest(ctx, "WINNERS\n"+c.config.ID)
		if err != nil {
			return
		}

		if response == "PENDING" {
			time.Sleep(200 * time.Millisecond)
			continue
		}

		parts := strings.Split(response, "|")
		if len(parts) < 2 || parts[0] != "WINNERS" {
			return
		}

		count, err := strconv.Atoi(parts[1])
		if err != nil {
			return
		}

		log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %v", count)
		return
	}
}

func (c *Client) sendRequest(ctx context.Context, payload string) (string, error) {
	if err := c.createClientSocket(); err != nil {
		return "", err
	}
	defer c.closeClientSocket()

	if err := SendMessage(c.conn, []byte(payload)); err != nil {
		if ctx.Err() != nil {
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			return "", nil
		}
		return "", err
	}

	response, err := RecvMessage(c.conn)
	if err != nil {
		if ctx.Err() != nil {
			log.Infof("action: shutdown | result: success | client_id: %v | signal: SIGTERM", c.config.ID)
			return "", nil
		}
		return "", err
	}

	return string(response), nil
}

func (c *Client) loadAgencyBets() ([][]string, error) {
	filePath := filepath.Join("/data", fmt.Sprintf("agency-%s.csv", c.config.ID))
	file, err := os.Open(filePath)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	reader := csv.NewReader(file)
	bets := make([][]string, 0)

	for {
		record, err := reader.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}

		if len(record) != 5 {
			return nil, fmt.Errorf("invalid bet format")
		}

		bets = append(bets, record)
	}

	return bets, nil
}
