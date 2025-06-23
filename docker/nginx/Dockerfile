FROM nginx:alpine

# Remove default config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/

# Create directories for static files
RUN mkdir -p /app/staticfiles /app/media

# Set permissions
RUN chown -R nginx:nginx /app

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"] 