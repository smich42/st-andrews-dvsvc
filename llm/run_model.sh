#!/bin/bash

MODEL_NAME=${1:-dvsvc-llm}

ollama serve &
ollama create ${MODEL_NAME} -f $(dirname "$0")/Modelfile
ollama run $MODEL_NAME