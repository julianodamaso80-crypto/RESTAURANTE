FROM nginx:alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy static files
COPY index.html    /usr/share/nginx/html/
COPY login.html    /usr/share/nginx/html/
COPY robots.txt    /usr/share/nginx/html/
COPY sitemap.xml   /usr/share/nginx/html/
COPY assets/       /usr/share/nginx/html/assets/

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
