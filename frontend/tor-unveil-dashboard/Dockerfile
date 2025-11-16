# ========= FRONTEND BUILD STAGE =========
FROM node:18-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build


# ========= PRODUCTION SERVE STAGE =========
FROM node:18-alpine
WORKDIR /app

RUN npm install -g serve

COPY --from=build /app/build ./build
COPY static.json ./static.json

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]
