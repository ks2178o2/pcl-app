# PitCrew Labs Frontend - Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY apps/realtime-gateway/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY apps/realtime-gateway/ .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY apps/realtime-gateway/nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    ARG HEALTHCHECK_URL
    ENV HEALTHCHECK_URL=${HEALTHCHECK_URL}
    CMD curl -f ${HEALTHCHECK_URL:-http://localhost/health} || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
