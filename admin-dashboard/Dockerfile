FROM node:20-alpine

WORKDIR /app

# Install dependencies first (leverages Docker layer caching)
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts

# Copy source
COPY . .

# Build Next.js for production
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]
