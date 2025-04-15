# AgentOS Fusion – Deploy via Railway

## Backend (FastAPI)
1. Crie um novo projeto no Railway
2. Escolha o backend (promptos_backend) com este Dockerfile
3. Adicione variáveis de ambiente:
   - JWT_SECRET_KEY
   - MONGO_URI
   - REDIS_URL

## Frontend (React/Vite)
1. Crie outro projeto no Railway
2. Use o diretório fusion_app com este Dockerfile
3. Adicione:
   - VITE_API_URL=https://backend-url.up.railway.app

## Serviços adicionais
- Use o botão "Add Plugin" no Railway para Redis e MongoDB
