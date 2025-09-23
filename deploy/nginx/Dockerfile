FROM nginx:alpine

# Copy the Nginx virtual host configuration into the image
# Build context is the deploy/ directory (set in compose)
COPY conf.d/default.conf /etc/nginx/conf.d/default.conf

