#!/bin/bash
# =============================================================================
# Kita.dev VPS Setup Script
# One-click deployment to a fresh Ubuntu VPS
# =============================================================================
# Usage: curl -fsSL https://raw.githubusercontent.com/user/kita.dev/main/deploy/setup.sh | bash
# =============================================================================

set -e

echo "🚀 Kita.dev VPS Setup"
echo "====================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (sudo)"
  exit 1
fi

# -----------------------------------------------------------------------------
# System Updates
# -----------------------------------------------------------------------------
echo "📦 Updating system packages..."
apt-get update && apt-get upgrade -y

# -----------------------------------------------------------------------------
# Install Docker
# -----------------------------------------------------------------------------
echo "🐳 Installing Docker..."
if ! command -v docker &> /dev/null; then
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker
  systemctl start docker
else
  echo "Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
  apt-get install -y docker-compose-plugin
fi

# -----------------------------------------------------------------------------
# Create Kita User
# -----------------------------------------------------------------------------
echo "👤 Creating kita user..."
if ! id "kita" &>/dev/null; then
  useradd -m -s /bin/bash kita
  usermod -aG docker kita
fi

# -----------------------------------------------------------------------------
# Clone Repository
# -----------------------------------------------------------------------------
INSTALL_DIR="/opt/kita.dev"
echo "📂 Setting up in $INSTALL_DIR..."

if [ -d "$INSTALL_DIR" ]; then
  echo "Directory exists, pulling latest..."
  cd $INSTALL_DIR && git pull
else
  git clone https://github.com/user/kita.dev.git $INSTALL_DIR
fi

cd $INSTALL_DIR
chown -R kita:kita $INSTALL_DIR

# -----------------------------------------------------------------------------
# Environment Setup
# -----------------------------------------------------------------------------
if [ ! -f ".env" ]; then
  echo "📝 Creating .env file..."
  cp .env.example .env
  echo ""
  echo "⚠️  IMPORTANT: Edit /opt/kita.dev/.env with your configuration!"
  echo "    Required: OPENAI_API_KEY, GITHUB_APP_ID, etc."
  echo ""
fi

# -----------------------------------------------------------------------------
# Firewall Setup
# -----------------------------------------------------------------------------
echo "🔥 Configuring firewall..."
if command -v ufw &> /dev/null; then
  ufw allow 22/tcp   # SSH
  ufw allow 80/tcp   # HTTP
  ufw allow 443/tcp  # HTTPS
  ufw --force enable
fi

# -----------------------------------------------------------------------------
# Build and Start
# -----------------------------------------------------------------------------
echo "🏗️ Building and starting services..."
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo ""
echo "✅ Kita.dev installation complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit /opt/kita.dev/.env with your configuration"
echo "   2. Set DOMAIN to your domain name"
echo "   3. Restart: cd /opt/kita.dev && docker compose -f docker-compose.prod.yml up -d"
echo "   4. Configure DNS to point to this server"
echo ""
echo "🔗 Dashboard will be available at: https://your-domain.com"
echo ""
