#!/bin/bash
set -e

# ---------------------------
# CONFIGURATION
# ---------------------------
APP_USER="appuser"
APP_DIR="/opt/apexmotors"
REPO_URL="https://github.com/ramazan-qandaxov/apexmotors.git"
SERVICE_NAME="docker-compose-app"
DB_SQL_FILE="$APP_DIR/db.sql"
ENV_FILE="$APP_DIR/.env"
CERT_DIR="/etc/ssl/apexmotors"
DOMAIN="localhost"

# ---------------------------
# REQUIRE ROOT
# ---------------------------
if [[ $EUID -ne 0 ]]; then
   echo "❌ This script must be run as root"
   exit 1
fi

# ---------------------------
# CREATE APP USER
# ---------------------------
if ! id "$APP_USER" &>/dev/null; then
    echo "👤 Creating user $APP_USER..."
    useradd -m -s /bin/bash "$APP_USER"
fi
usermod -aG docker "$APP_USER"

# ---------------------------
# INSTALL DEPENDENCIES
# ---------------------------
echo "📦 Installing dependencies..."
apt update
apt install -y git docker.io docker-compose openssl
systemctl enable --now docker

# ---------------------------
# CLONE OR UPDATE REPO
# ---------------------------
if [ ! -d "$APP_DIR/.git" ]; then
    echo "📥 Cloning repository into $APP_DIR..."
    rm -rf "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
else
    echo "🔄 Updating existing repository..."
    cd "$APP_DIR"
    sudo -u "$APP_USER" git pull
fi

# ---------------------------
# ASK FOR .env VARIABLES
# ---------------------------
read -p "Enter PostgreSQL database name [apexmotors]: " POSTGRES_DB
POSTGRES_DB=${POSTGRES_DB:-apexmotors}

read -p "Enter PostgreSQL username [apexmotors]: " POSTGRES_USER
POSTGRES_USER=${POSTGRES_USER:-apexmotors}

read -s -p "Enter PostgreSQL password [veryverysecurepassword]: " POSTGRES_PASSWORD
echo
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-veryverysecurepassword}

# ---------------------------
# CREATE .env FILE
# ---------------------------
echo "⚙️ Creating .env file..."
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
    echo "🔐 Creating self-signed SSL certificates..."
    mkdir -p "$CERT_DIR"
    openssl req -x509 -nodes -days 365 \
        -subj "/CN=$DOMAIN" \
        -newkey rsa:2048 \
        -keyout "$CERT_DIR/server.key" \
        -out "$CERT_DIR/server.crt"
    chown -R "$APP_USER:$APP_USER" "$CERT_DIR"
fi

# ---------------------------
# CREATE SYSTEMD SERVICE
# ---------------------------
echo "⚙️ Setting up systemd service..."
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
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

# ---------------------------
# DATABASE IMPORT
# ---------------------------
if [ -f "$DB_SQL_FILE" ]; then
    echo "🗄️ Waiting for PostgreSQL to become healthy..."
    for i in {1..30}; do
        if docker compose -f "$APP_DIR/docker-compose.yml" exec -T db pg_isready -U "$POSTGRES_USER" &>/dev/null; then
            echo "✅ PostgreSQL is ready!"
            break
        fi
        sleep 2
    done

    echo "📥 Importing database from db.sql..."
    docker compose -f "$APP_DIR/docker-compose.yml" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DB_SQL_FILE" || {
        echo "⚠️ Database import failed"
    }
fi

echo "✅ Installation complete!"
echo "➡️ Service: $SERVICE_NAME"
echo "➡️ SSL certificates: $CERT_DIR"
echo "➡️ App directory: $APP_DIR"
