#!/bin/bash

MODEL_NAME=${1:-dvsvc-llm}

ollama serve &
SERVER_PID=$!

sleep 5

if ! ollama list | grep -q "^${MODEL_NAME}"; then
    ollama create ${MODEL_NAME} -f $(dirname "$0")/Modelfile
fi

echo "Sleeping"
sleep 86400

