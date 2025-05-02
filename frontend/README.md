# Fusion App - Frontend  
Frontend React (Vite + Tailwind CSS) para o sistema AgentOS Core / VoulezVous.  
## Visão Geral  
Este aplicativo web fornece a interface do usuário principal para interagir com o backend AgentOS Core. Ele implementa a visão "Fusion Flip", oferecendo duas interfaces principais integradas:  
1.  **Comms:** Uma interface estilo WhatsApp otimizada para comunicação operacional (mensagens, status, interações com clientes/equipe).  
2.  **Advisor:** Uma interface estilo ChatGPT para interação com a IA central do sistema (Semantic LLM Engine), permitindo consultas em linguagem natural, execução de comandos e visualização de dados complexos de forma inteligível.  
O layout inclui um menu de navegação principal à esquerda e um painel dinâmico de "Fusion Hints" à direita, fornecendo sugestões contextuais da IA em tempo real.  
## Tecnologias Utilizadas  
*   **Framework/Lib:** React 18+  
*   **Build Tool:** Vite  
*   **Estilização:** Tailwind CSS  
*   **Roteamento:** React Router DOM v6  
*   **Requisições API:** Axios  
*   **Animações:** Framer Motion  
*   **Renderização Markdown:** React Markdown + Remark GFM  
*   **Highlight de Código:** React Syntax Highlighter  
*   **Formatação de Data:** date-fns  
*   **Ícones:** Heroicons (@heroicons/react)  
*   **IDs Únicos (Frontend):** uuid  
*   **Gerenciamento de Estado (Básico):** React Context API (para Auth e WebSocket)  
*   **Testes:** Vitest, React Testing Library, Cypress (para E2E)  
## Configuração do Ambiente de Desenvolvimento  
1.  **Pré-requisitos:**  
    *   Node.js (v18 LTS ou superior recomendado)  
    *   npm, yarn ou pnpm  
    *   Backend `agentos_core` configurado e rodando localmente ou em um ambiente acessível.  
2.  **Instalar Dependências:**  
    Na raiz do projeto `fusion-app`, execute:  
    ```bash  
    npm install  
    # ou: yarn install  
    # ou: pnpm install  
    ```  
3.  **Configurar Variáveis de Ambiente:**  
    *   Copie o arquivo `.env.example` para `.env`:  
        ```bash  
        cp .env.example .env  
        ```  
    *   Edite o arquivo `.env` e defina as seguintes variáveis:  
        *   `VITE_BACKEND_BASE_URL`: URL base completa da API do `agentos_core` (incluindo `/api/v1`). Ex: `http://localhost:8000/api/v1`  
        *   `VITE_WS_BASE_URL`: URL base completa do WebSocket do `agentos_core` (incluindo `/ws/updates`). Ex: `ws://localhost:8000/ws/updates`  
        *   `VITE_STATIC_API_KEY`: A chave API estática *exata* definida na variável `API_KEY` no `.env` do backend. Usada para autenticar a conexão WebSocket.  
## Executando a Aplicação  
*   **Modo de Desenvolvimento (com Hot Reload):**  
    ```bash  
    npm run dev  
    # ou: yarn dev  
    # ou: pnpm dev  
    ```  
    Acesse a aplicação no endereço fornecido pelo Vite (geralmente `http://localhost:5173`).  
*   **Build para Produção:**  
    ```bash  
    npm run build  
    # ou: yarn build  
    # ou: pnpm build  
    ```  
    Os arquivos otimizados para produção serão gerados na pasta `dist/`.  
*   **Preview da Build de Produção:**  
    ```bash  
    npm run preview  
    # ou: yarn preview  
    # ou: pnpm preview  
    ```  
    Inicia um servidor local simples para servir os arquivos da pasta `dist/`.  
## Scripts Disponíveis  
*   `dev`: Inicia o servidor de desenvolvimento Vite.  
*   `build`: Gera a build otimizada para produção.  
*   `lint`: Executa o ESLint para análise estática do código.  
*   `preview`: Previsualiza a build de produção.  
*   `test`: Roda os testes unitários e de integração com Vitest.  
*   `coverage`: Roda os testes com Vitest e gera um relatório de cobertura.  
*   `(Se Cypress configurado) cypress:open`: Abre o runner interativo do Cypress E2E.  
*   `(Se Cypress configurado) cypress:run`: Roda os testes E2E em modo headless.  
