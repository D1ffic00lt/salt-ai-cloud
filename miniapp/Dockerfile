FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_SALTAI_CLOUD_API_BASE_URL=/api/v1
ENV VITE_SALTAI_CLOUD_API_BASE_URL=${VITE_SALTAI_CLOUD_API_BASE_URL}

COPY miniapp/package.json ./

RUN npm install

COPY miniapp/ ./

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html/miniapp
COPY miniapp/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80