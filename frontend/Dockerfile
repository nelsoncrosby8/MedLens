# MedLens frontend — dev image (docker-compose runs `vite --host` with the source
# bind-mounted; node_modules stays inside the container via an anonymous volume).
FROM node:22-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
