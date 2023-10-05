#!/bin/sh

PORT="${VECTORDB_SERVICE_INNER_PORT}"
echo "Health check started; accessing http://localhost:$PORT ..."
response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT")

if [ "$response" = "200" ]; then
  echo "Health check passed: Response code is $response"
  exit 0
else
  echo "Health check failed: Unable to access http://localhost:$PORT. Response: $response"
  exit 1
fi