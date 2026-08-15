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
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml turbo.json ./

# Copy apps and packages so pnpm can resolve workspace deps
COPY apps/ ./apps/
COPY packages/ ./packages/

# Install all workspace packages
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile

# Public API URL is baked at build time (client-side constant)
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ARG NEXT_PUBLIC_USE_DEMO_DATA=false
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_USE_DEMO_DATA=$NEXT_PUBLIC_USE_DEMO_DATA

# Build the Next.js app with standalone output
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm --filter @yenimenzil/web build

# Production runtime stage
FROM node:20-slim AS production

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME=0.0.0.0

RUN groupadd -r appuser && useradd -r -g appuser --create-home appuser

WORKDIR /home/app

# Standalone output preserves the monorepo layout: the app entry point is at
# apps/web/server.js (not ./server.js) because @yenimenzil/web lives in apps/web.
COPY --from=builder /home/app/apps/web/.next/standalone ./
COPY --from=builder /home/app/apps/web/.next/static ./apps/web/.next/static

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=5 \
  CMD node -e "fetch('http://127.0.0.1:3000/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "apps/web/server.js"]
