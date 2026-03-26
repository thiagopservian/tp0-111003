package common

import (
	"encoding/binary"
	"fmt"
	"net"
)

func SendAll(conn net.Conn, data []byte) error {
	for len(data) > 0 {
		n, err := conn.Write(data)
		if err != nil {
			return err
		}
		data = data[n:]
	}
	return nil
}

func RecvAll(conn net.Conn, n int) ([]byte, error) {
	buf := make([]byte, n)
	offset := 0
	for offset < n {
		read, err := conn.Read(buf[offset:])
		if err != nil {
			return nil, err
		}
		offset += read
	}
	return buf, nil
}

func SendMessage(conn net.Conn, payload []byte) error {
	header := make([]byte, 4)
	binary.BigEndian.PutUint32(header, uint32(len(payload)))
	if err := SendAll(conn, header); err != nil {
		return fmt.Errorf("failed to send header: %w", err)
	}
	if err := SendAll(conn, payload); err != nil {
		return fmt.Errorf("failed to send payload: %w", err)
	}
	return nil
}

func RecvMessage(conn net.Conn) ([]byte, error) {
	header, err := RecvAll(conn, 4)
	if err != nil {
		return nil, fmt.Errorf("failed to read header: %w", err)
	}
	length := binary.BigEndian.Uint32(header)
	payload, err := RecvAll(conn, int(length))
	if err != nil {
		return nil, fmt.Errorf("failed to read payload: %w", err)
	}
	return payload, nil
}
