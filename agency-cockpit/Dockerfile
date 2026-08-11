# Agency Cockpit — multi-target packaging
FROM nginx:1.27-alpine
COPY dist/ /usr/share/nginx/html/
COPY deploy/nginx-spa.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
HEALTHCHECK CMD wget -qO- http://127.0.0.1/ || exit 1
