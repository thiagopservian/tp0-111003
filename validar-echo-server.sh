#!/bin/sh

NETWORK="tp0_testing_net"
SERVER_HOST="server"
SERVER_PORT="12345"
TEST_MESSAGE="echo_server_test_message"

RESPONSE=$(printf "%s\n" "$TEST_MESSAGE" | docker run --rm -i --network "$NETWORK" busybox:1.36 sh -c "nc -w 3 $SERVER_HOST $SERVER_PORT" 2>/dev/null)
STATUS=$?

if [ $STATUS -ne 0 ]; then
  echo "action: test_echo_server | result: fail"
  exit 0
fi

RESPONSE=$(printf "%s" "$RESPONSE" | tr -d '\r' | head -n 1)

if [ "$RESPONSE" = "$TEST_MESSAGE" ]; then
  echo "action: test_echo_server | result: success"
else
  echo "action: test_echo_server | result: fail"
fi
