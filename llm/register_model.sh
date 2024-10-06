#!/bin/zsh

MODEL_NAME=${1:-dvsvc-llm}
ollama create ${MODEL_NAME} -f ./Modelfile
