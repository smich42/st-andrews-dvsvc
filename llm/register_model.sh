#!/bin/bash

MODEL_NAME=${1:-dvsvc-llm}
ollama create ${MODEL_NAME} -f $(dirname "$0")/Modelfile
