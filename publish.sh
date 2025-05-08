#!/bin/bash

IMAGE_NAME="voulezvous-ai/agentos"
TAG="latest"

echo "🔧 Buildando imagem Docker..."
docker build -t $IMAGE_NAME:$TAG .

echo "🔐 Autenticando no Docker Hub..."
docker login

echo "📦 Enviando imagem para o Docker Hub..."
docker push $IMAGE_NAME:$TAG

echo "✅ Publicado como $IMAGE_NAME:$TAG"
