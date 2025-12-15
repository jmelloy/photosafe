FROM node:20-alpine

WORKDIR /app

# Install git for git SHA capture
RUN apk add --no-cache git

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app (git SHA will be captured by vite.config.ts)
RUN npm run build

# Expose port
EXPOSE 5173

# Run the app
CMD ["npm", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
