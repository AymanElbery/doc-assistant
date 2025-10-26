# Build stage
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --legacy-peer-deps

# Copy source code
COPY . .

# Build application for production
RUN npm run build --configuration=production

# Production stage
FROM nginx:alpine

# Copy built application (Angular 19+ uses /browser output)
COPY --from=build /app/dist/ai-docs-assistant /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]