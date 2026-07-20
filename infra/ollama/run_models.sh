#!/bin/bash

# Startet den Ollama-Server im Hintergrund
ollama serve &

# Wartet, bis der Ollama-Server vollständig erreichbar ist
echo "Warte auf Ollama-Server..."
while ! ollama list >/dev/null 2>&1; do
  sleep 1
done

echo "Lade qwen2.5:7b herunter..."
ollama pull qwen2.5:7b

echo "Erstelle Custom-Modell ..."
ollama create hr-analyst -f /Modelfile

# Hält den Container am Leben und bringt den Ollama-Prozess in den Vordergrund
wait -n
