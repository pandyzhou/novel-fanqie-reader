FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json /app/
RUN npm install --no-fund --no-audit --registry=https://registry.npmmirror.com
COPY . /app
RUN npm run build-only

FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
