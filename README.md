# 3D Printing Quality Monitoring System 🖨️📊

[![Docker](https://img.shields.io/badge/Docker-2CA5E0?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![MQTT](https://img.shields.io/badge/MQTT-3C5280?style=flat&logo=eclipse-mosquitto&logoColor=white)](https://mqtt.org/)
[![Grafana](https://img.shields.io/badge/Grafana-F46800?style=flat&logo=grafana&logoColor=white)](https://grafana.com/)

A real-time monitoring system for 3D printers with automated quality control using MQTT, machine learning, and Grafana dashboards.

## Key Features ✨

- Real-time printer monitoring (physical or simulated)
- Anomaly detection using ML models
- Automated parameter adjustment
- Beautiful Grafana dashboards
- Containerized deployment (Docker)

## Quick Start 🚀

### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.12+

### Installation
```bash
git clone https://github.com/yourrepo/3d-printing-mlops.git
cd 3d-printing-mlops

# Set up environment
cp .env.example .env
nano .env  # Edit configuration

# Initialize MQTT authentication
chmod +x scripts/init_mqtt.sh
./scripts/init_mqtt.sh

# Start the system
docker-compose up -d --build
```

## Access Services 🔍

| Service    | URL                  | Default Credentials  |
|------------|----------------------|----------------------|
| Grafana    | http://localhost:3000 | `admin/grafanapass` |
| InfluxDB   | http://localhost:8086 | `admin/influxpass`  |

## Usage Examples 💻

**View real-time data stream**:
```bash
docker-compose exec mqtt mosquitto_sub -t 'printing/#' -v
```

**Send test command**:
```bash
docker-compose exec mqtt mosquitto_pub -t 'printer/control/1' -m '{"speed":50}'
```

**Check system health**:
```bash
docker-compose ps
```

## Project Structure 📂
```
├── config/           # Service configurations
├── dashboard/        # Grafana dashboards
├── data/             # Sample datasets
├── real-time-engine/ # ML processing
├── synthesizer/      # Data simulator
├── scripts/          # Utility scripts
├── docker-compose.yml# Deployment config
└── .env              # Environment variables
```

## Troubleshooting 🐛

**MQTT Connection Issues**:
```bash
docker-compose logs mqtt
```

**Missing Data in Grafana**:
```bash
docker-compose exec influxdb influx query 'from(bucket:"printing_metrics") |> range(start:-1h)'
```

## Documentation 📚

For full documentation including architecture diagrams and API details, see:  
[📘 Detailed Documentation](docs/ARCHITECTURE.md)

## License 📜

MIT License - See [LICENSE](LICENSE) for details.
```

### Key Elements Included:

1. **Visual Badges** - Quick tech stack identification
2. **Quick Start Section** - Minimal setup instructions
3. **Service Access Table** - All key URLs in one place
4. **Common Commands** - Ready-to-copy usage examples
5. **Troubleshooting** - Common issues and solutions
6. **Structured Layout** - Clear file organization
7. **Documentation Link** - Connection to full docs

The README focuses on:
- Getting users running quickly
- Essential daily commands
- Clear troubleshooting
- Visual organization
- Links to deeper documentation.
