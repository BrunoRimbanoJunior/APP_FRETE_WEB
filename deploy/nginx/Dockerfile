FROM nginx:1.31.3-alpine@sha256:4a73073bd557c65b759505da037898b61f1be6cbcc3c2c3aeac22d2a470c1752

# Copy the Nginx virtual host configuration into the image
# Build context is the deploy/ directory (set in compose)
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O /dev/null http://127.0.0.1/nginx-health || exit 1
