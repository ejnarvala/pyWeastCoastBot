## Raspberry Pi Deployment

### Prerequisites

- Docker and Docker Compose installed on the Raspberry Pi (see [Docker Installation Guide](https://docs.docker.com/engine/install/debian))
- User has sudo access
- Git repository cloned to access configuration files

This has been tested with a raspberry pi zero 2 W, running Raspberry Pi OS Lite (Bookworm 64)

### Installation

#### 1. Set up deployment directory

```bash
sudo mkdir -p /opt/pyweastcoastbot
sudo chown $USER:$USER /opt/pyweastcoastbot
```

#### 2. Copy configuration files

From the repository root, copy the required files:

```bash
cp /pi/compose.rpi.yml /opt/pyweastcoastbot/compose.yml
cp /pi/pyweastcoastbot.service /tmp/pyweastcoastbot.service
```

#### 3. Create environment file

Create `/opt/pyweastcoastbot/.env` with your bot's configuration:

```bash
cat > /opt/pyweastcoastbot/.env << 'EOF'
BOT_TOKEN=<your_bot_token_here>
API_KEY=<your_api_key_here>
DEBUG=false
EOF
```

**Important:** Keep `.env` private — it contains secrets.

#### 4. Install systemd service

```bash
sudo cp /pi/pyweastcoastbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pyweastcoastbot
sudo systemctl start pyweastcoastbot
```

#### 5. Verify deployment

Check service status:

```bash
sudo systemctl status pyweastcoastbot
```

View running containers:

```bash
docker compose -f /opt/pyweastcoastbot/compose.yml ps
```

### Management

#### View logs

```bash
journalctl -u pyweastcoastbot -f
```

Or view container logs directly:

```bash
docker compose -f /opt/pyweastcoastbot/compose.yml logs -f
```

#### Manual updates

Watchtower automatically checks every 5 minutes for image updates. To manually update, restart the service or manage it directly with docker referencing the compose file in /opt/pyweastcoastbot/compose.yml

#### Restart service

```bash
sudo systemctl restart pyweastcoastbot
```

#### Stop service

```bash
sudo systemctl stop pyweastcoastbot
```

### Notes

- The deployment uses `compose.rpi.yml` which includes the bot and Watchtower for automatic updates
- The systemd service (`pyweastcoastbot.service`) manages the Docker Compose stack
- Logs are available via journald and Docker logging
- Compatible with 64-bit Raspberry Pi OS; ARMv7 images work on Pi Zero 2 W

