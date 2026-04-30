# ---- build stage ----
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --prefer-offline --no-audit

COPY . .

ARG GIT_SHA=unknown
ENV GIT_SHA=${GIT_SHA}

# Build the app
# Note: GIT_SHA is captured from build arg by vite.config.ts (no git needed)
RUN npm run build

# ---- serve stage ----
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
