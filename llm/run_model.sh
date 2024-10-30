#!/bin/bash

MODEL_NAME=${1:-dvsvc-llm}

ollama serve &
until /bin/curl -s http://localhost:11434/api/tags >/dev/null; do
    sleep 2
done

if ! ollama list | grep -q "^${MODEL_NAME}"; then
    ollama create ${MODEL_NAME} -f $(dirname "$0")/Modelfile
fi

pkill ollama
exec ollama serve
