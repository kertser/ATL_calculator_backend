#!/bin/bash
set -e  # Exit on any error

echo "🚀 Starting UV Calculator deployment/update..."

#--------------------------------------
# 1. Check & install dependencies only if missing
#--------------------------------------
install_if_missing() {
    if ! command -v "$1" >/dev/null 2>&1; then
        echo "📦 Installing $1..."
        sudo apt update -y
        sudo apt install -y "$1"
    else
        echo "✅ $1 already installed."
    fi
}

install_if_missing nginx
install_if_missing docker
install_if_missing docker-compose
install_if_missing curl

#--------------------------------------
# 2. Ensure directories exist
#--------------------------------------
echo "📁 Ensuring necessary directories exist..."
sudo mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled /var/www/calculator
sudo chown -R $USER:$USER /var/www/calculator

#--------------------------------------
# 3. Write Nginx config only if missing or different
#--------------------------------------
NGINX_CONF_PATH="/etc/nginx/sites-available/calculator"
TMP_CONF="/tmp/calculator-nginx.conf"

cat > "$TMP_CONF" <<'EOF'
server {
    listen 9876;
    server_name _;

    root /var/www/calculator;
    index index.html;

    # -------------------------------
    # FRONTEND (static build)
    # -------------------------------
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Static assets: cache aggressively
    location ~* \.(?:js|mjs|css|png|jpg|jpeg|gif|svg|ico|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;

    # -------------------------------
    # BACKEND (FastAPI container)
    # -------------------------------
    location /api/ {
        proxy_pass http://127.0.0.1:5000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
    }
}
EOF

if [ ! -f "$NGINX_CONF_PATH" ]; then
    echo "📝 Creating new Nginx site configuration..."
    sudo mv "$TMP_CONF" "$NGINX_CONF_PATH"
else
    if ! cmp -s "$TMP_CONF" "$NGINX_CONF_PATH"; then
        echo "🔄 Updating Nginx configuration (changes detected)..."
        sudo mv "$TMP_CONF" "$NGINX_CONF_PATH"
    else
        echo "✅ Nginx configuration already up-to-date."
        rm "$TMP_CONF"
    fi
fi

if [ ! -L /etc/nginx/sites-enabled/calculator ]; then
    sudo ln -s /etc/nginx/sites-available/calculator /etc/nginx/sites-enabled/
fi

echo "🔍 Testing nginx configuration..."
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload nginx
echo "✅ Nginx ready."

#--------------------------------------
# 4. Backend Deployment
#--------------------------------------
DEPLOY_DIR="$HOME/Projects/Calculator/server"
echo "📦 Deploying backend to $DEPLOY_DIR"

sudo mkdir -p "$DEPLOY_DIR"
sudo chown -R $USER:$USER "$DEPLOY_DIR"
cd "$DEPLOY_DIR"

if [ -d ".git" ]; then
    echo "📥 Pulling latest backend code..."
    git pull origin master
else
    echo "📦 Cloning backend repository..."
    git clone https://github.com/kertser/ATL_calculator_backend.git .
fi

echo "🐳 Rebuilding and starting Docker containers..."
docker-compose down --remove-orphans || true
docker-compose build --pull
docker-compose up -d

#--------------------------------------
# 5. Health check
#--------------------------------------
echo "⏳ Waiting for API to start..."
for i in {1..6}; do
    if curl -fs http://localhost:5000/health > /dev/null; then
        echo "✅ API is healthy and reachable."
        break
    else
        echo "⏳ Attempt $i/6 — waiting 5s..."
        sleep 5
        if [ $i -eq 6 ]; then
            echo "❌ API failed to respond after 30s."
            docker-compose logs --tail=20
            exit 1
        fi
    fi
done

#--------------------------------------
# 6. Final summary
#--------------------------------------
SERVER_IP=$(hostname -I | awk '{print $1}')
echo "🎉 Deployment complete!"
echo "Frontend available at: http://$SERVER_IP:9876"
echo "Backend proxied at:   http://$SERVER_IP/api/"
