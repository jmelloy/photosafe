# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

ARG GIT_SHA=unknown
ENV GIT_SHA=${GIT_SHA}

# Build the app (git SHA will be captured by vite.config.ts)
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install vite for preview server (minimal production setup)
RUN npm install vite@^7.3.0

# Copy built files from builder stage
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Run the preview server
CMD ["npx", "vite", "preview", "--host", "0.0.0.0", "--port", "5173"]
