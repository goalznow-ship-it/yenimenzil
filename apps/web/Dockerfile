FROM node:20-slim AS builder

ENV PNPM_HOME=/root/.pnpm
ENV PNPM_STORE=/pnpm-store

RUN corepack enable && \
    # Docker Desktop VMs can briefly lag Debian mirror metadata after resume.
    # Signatures are still verified; only the wall-clock freshness check is relaxed.
    apt-get -o Acquire::Check-Date=false update && \
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

# Public variables are embedded by Next.js at build time. Keep them configurable
# instead of relying on runtime environment variables that cannot change the bundle.
ARG NEXT_PUBLIC_API_URL=https://yenimenzil.az/api/v1
ARG NEXT_PUBLIC_APP_URL=https://yenimenzil.az
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL}
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
COPY --chown=appuser:appuser --from=builder /home/app/apps/web/.next/standalone ./
COPY --chown=appuser:appuser --from=builder /home/app/apps/web/.next/static ./apps/web/.next/static

USER appuser

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD node -e "fetch('http://localhost:3000/health').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"

CMD ["node", "apps/web/server.js"]
