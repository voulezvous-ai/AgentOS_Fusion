FROM node:20-slim AS builder
WORKDIR /app
COPY fusion_app/package*.json ./
RUN npm ci
COPY fusion_app .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app .
ENV PORT=3000
EXPOSE 3000
CMD ["npm", "run", "preview", "--", "--port", "3000", "--host"]
