# Frontend Dockerfile
# Serves the static, dependency-free Campus Assistant UI (index.html) via nginx.
# nginx proxies /health, /chat and /api/ to the backend-api service, so the UI
# talks to the backend on the same origin.
FROM nginx:alpine

# Static site + assets
COPY index.html /usr/share/nginx/html/index.html
COPY public/ /usr/share/nginx/html/

# nginx configuration (listens on 3008, proxies API to backend-api)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 3008

# Health check (busybox wget ships with the nginx:alpine image)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget -q --spider http://localhost:3008/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
