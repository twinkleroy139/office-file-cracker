FROM php:8.2-cli

# Install Python and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Install required Python cracking libraries
RUN pip3 install msoffcrypto-tool --break-system-packages

# Set working directory
WORKDIR /var/www/html

# Copy all project files into the container
COPY . .

# Ensure logs, uploads, and wordlists directories exist with write permissions
RUN mkdir -p logs uploads wordlists && chmod -R 777 logs uploads wordlists

# Render assigns a dynamic port via the PORT environment variable
EXPOSE 8080

# Start PHP built-in server bound to Render's port
CMD ["sh", -c, "php -S 0.0.0.0:${PORT:-8080} -t ."]