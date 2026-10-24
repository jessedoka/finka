FROM node:22-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ENV NODE_ENV=production
RUN npm run build

RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 3000
CMD ["npm", "start"]
