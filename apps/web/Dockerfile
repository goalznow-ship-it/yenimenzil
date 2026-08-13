FROM node:22-alpine AS builder

# Set working directory
WORKDIR /app

# Install dependencies (build deps only)
COPY apps/web/package.json apps/web/pnpm-lock.yaml ./
RUN npm install --frozen-lockfile

# Copy source code
COPY apps/web/src ./src
COPY apps/web/tsconfig.json ./
COPY apps/web/next.config.ts ./
COPY apps/web/tailwind.config.mjs ./
COPY apps/web/postcss.config.mjs ./
COPY apps/web/globals.css ./

# Build Next.js app
RUN npm run build

# Production stage
FROM node:22-alpine

# Create app user
RUN addgroup -S node && adduser -S -g node app

WORKDIR /app

# Set production environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Copy built files from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Set the correct permission on app directory
RUN chown -R node:node /app

# Switch to non-root user
USER app

# Expose the app port
EXPOSE 3000

# Start the application using next start
CMD ["npm", "start"]