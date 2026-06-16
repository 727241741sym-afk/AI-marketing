FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json apps/web/package.json
RUN npm ci --workspace apps/web

FROM node:22-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY apps/web ./apps/web
WORKDIR /app/apps/web
ARG API_BASE_URL=http://localhost:8000
ENV API_BASE_URL=$API_BASE_URL
RUN npm run build

FROM node:22-alpine AS runner
ENV NODE_ENV=production
WORKDIR /app/apps/web
RUN addgroup -S nextjs && adduser -S nextjs -G nextjs
COPY --from=builder /app/node_modules /app/node_modules
COPY --from=builder /app/apps/web/.next ./.next
COPY --from=builder /app/apps/web/public ./public
COPY --from=builder /app/apps/web/package.json ./package.json
USER nextjs
EXPOSE 3000
CMD ["node", "/app/node_modules/next/dist/bin/next", "start"]
