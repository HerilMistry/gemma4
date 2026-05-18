FROM node:20-alpine

WORKDIR /app

# Copy package configuration files
COPY package.json package-lock.json* ./

# Install packages clean
RUN npm ci

# Copy the rest of the application
COPY . .

# Set environment variables for production build
# NEXT_PUBLIC_* vars must be set at BUILD time
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_TELEMETRY_DISABLED=1

# Build the Next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Start server using the standalone build
CMD ["node", ".next/standalone/server.js"]
