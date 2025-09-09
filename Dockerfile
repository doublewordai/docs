FROM node:18-alpine AS base

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

EXPOSE 3000
CMD ["sh", "-c", "npm start -- --host 0.0.0.0"]
