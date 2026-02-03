# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --prefer-offline --no-audit

# Copy source code
COPY . .

ARG GIT_SHA=unknown
ENV GIT_SHA=${GIT_SHA}

# Build the app
# Note: GIT_SHA is captured from build arg by vite.config.ts (no git needed)
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Vite version can be overridden via build arg, defaults to version in package.json
ARG VITE_VERSION=^7.3.0

# Install only production dependencies and vite (needed for preview server)
# Separate commands to maintain lockfile integrity
RUN npm ci --omit=dev --no-save --prefer-offline --no-audit
RUN npm install --no-save vite@${VITE_VERSION}

# Copy built files from builder stage
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 5173

# Run the preview server
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
