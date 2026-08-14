FROM node:20-slim AS builder

ENV PNPM_HOME=/root/.pnpm
ENV PNPM_STORE=/pnpm-store

RUN corepack enable && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      python3 \
      make \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /home/app

# Copy root pnpm workspace manifests
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./

# Copy apps and packages so pnpm can resolve workspace deps
COPY apps/ ./apps/
COPY packages/ ./packages/

# Install all workspace packages (incl. @yenimenzil/config, @yenimenzil/ui, etc.)
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile

# Set production env vars for build
ENV NEXT_PUBLIC_USE_DEMO_DATA=false

# Build the Next.js app with standalone output
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm --filter @yenimenzil/web build

# Production runtime stage
FROM node:20-slim AS production

ENV NODE_ENV=production
ENV PORT=3000

RUN groupadd -r appuser && useradd -r -g appuser --create-home appuser

WORKDIR /home/app

# Copy only the standalone build output from builder
COPY --from=builder /home/app/apps/web/.next/standalone ./
COPY --from=builder /home/app/apps/web/.next/static ./.next/static
COPY --from=builder /home/app/apps/web/node_modules ./node_modules

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl -fsS http://localhost:3000/health || exit 1

CMD ["node", "server.js"]