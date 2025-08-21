#!/bin/bash
set -e

# ---------------------------
# CONFIGURATION
# ---------------------------
APP_USER="appuser"
APP_DIR="/opt/apexmotors"
REPO_URL="https://github.com/ramazan-qandaxov/apexmotors.git"
SERVICE_NAME="docker-compose-app"
ENV_FILE="$APP_DIR/.env"
CERT_DIR="/etc/ssl/apexmotors"
DOMAIN="localhost"

# ---------------------------
# REQUIRE ROOT
# ---------------------------
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root"
   exit 1
fi

# ---------------------------
# INSTALL DEPENDENCIES
# ---------------------------
echo "Installing dependencies..."
apt update -qq >/dev/null
apt install -y -qq git docker.io docker-compose openssl >/dev/null
systemctl enable --now docker >/dev/null

# ---------------------------
# CREATE APP USER
# ---------------------------
if ! id "$APP_USER" &>/dev/null; then
    echo "Creating user $APP_USER..."
    useradd -m -s /bin/bash "$APP_USER" >/dev/null
fi
usermod -aG docker "$APP_USER" >/dev/null

# ---------------------------
# CLONE OR UPDATE REPO
# ---------------------------
if [ ! -d "$APP_DIR/.git" ]; then
    echo "Cloning repository into $APP_DIR..."
    rm -rf "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR" >/dev/null 2>&1
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
else
    echo "Updating existing repository..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull >/dev/null 2>&1
fi

# ---------------------------
# ASK FOR .env VARIABLES
# ---------------------------
read -p "Enter PostgreSQL database name leave blank for default [apexmotors]: " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-apexmotors}

read -p "Enter PostgreSQL username leave blank for default [apexmotors]: " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-apexmotors}

read -s -p "Enter PostgreSQL password leave blank for default [veryverysecurepassword]: " POSTGRES_PASSWORD
echo
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-veryverysecurepassword}

# ---------------------------
# CREATE .env FILE
# ---------------------------
echo "Creating .env file..."
cat >"$ENV_FILE" <<EOF
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
EOF
chown "$APP_USER:$APP_USER" "$ENV_FILE"

# ---------------------------
# CREATE SSL CERTIFICATES
# ---------------------------
if [ ! -d "$CERT_DIR" ]; then
    echo "Creating self-signed SSL certificates..."
    mkdir -p "$CERT_DIR"
    openssl req -x509 -nodes -days 365 \
        -subj "/CN=$DOMAIN" \
        -newkey rsa:2048 \
        -keyout "$CERT_DIR/server.key" \
        -out "$CERT_DIR/server.crt" >/dev/null 2>&1
    chown -R "$APP_USER:$APP_USER" "$CERT_DIR"
fi

# ---------------------------
# CREATE SYSTEMD SERVICE
# ---------------------------
echo "Setting up systemd service..."
cat >"/etc/systemd/system/${SERVICE_NAME}.service" <<EOF
[Unit]
Description=Docker Compose Application
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$APP_DIR
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=$APP_USER
Group=docker

[Install]
WantedBy=multi-user.target
EOF

# ---------------------------
# ENABLE AND START SERVICE
# ---------------------------
systemctl daemon-reload >/dev/null
systemctl enable "$SERVICE_NAME" >/dev/null
systemctl restart "$SERVICE_NAME" >/dev/null

# ---------------------------
# WAIT FOR WEB CONTAINER TO BE READY
# ---------------------------
echo "Waiting for web container to start..."
sleep 10

# ---------------------------
# CREATE DJANGO SUPERUSER
# ---------------------------
echo "Creating Django superuser..."
docker-compose -f "$APP_DIR/docker-compose.yml" exec -T web python manage.py shell >/dev/null 2>&1 <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='superuser').exists():
    User.objects.create_superuser('superuser', 'admin@example.com', 'superpassword')
EOF
echo "Django superuser created: username=superuser, password=superpassword"

echo "Installation complete!"
echo "Service: $SERVICE_NAME"
echo "SSL certificates: $CERT_DIR"
echo "App directory: $APP_DIR"
