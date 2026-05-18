FROM node:18-alpine

WORKDIR /app

# Copy package configuration files
COPY package.json package-lock.json* ./

# Install packages clean
RUN npm ci

# Copy the rest of the application
COPY . .

# Set environment variables for production build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_PUBLIC_API_URL=http://localhost:8000

# Build the Next.js app
RUN npm run build

# Expose port
EXPOSE 3000

# Start server
CMD ["npm", "run", "start"]
