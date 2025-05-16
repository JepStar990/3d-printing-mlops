# 3D Printing Quality Monitoring System

## 📖 Table of Contents
1. [System Overview](#-system-overview)
2. [Architecture](#-architecture)
3. [Data Flow](#-data-flow)
4. [Installation](#-installation)
5. [Configuration](#-configuration)
6. [Usage](#-usage)
7. [API Documentation](#-api-documentation)
8. [Troubleshooting](#-troubleshooting)
9. [Future Enhancements](#-future-enhancements)

## 🌐 System Overview

A real-time monitoring system for 3D printers that:
- Collects sensor data via MQTT
- Processes data using machine learning
- Provides real-time feedback control
- Visualizes metrics in Grafana
- Simulates printers for development/testing

**Key Features**:
- Real-time anomaly detection
- Automated print parameter adjustment
- Historical trend analysis
- Multi-printer support
- Containerized deployment

## 🏗 Architecture

### Component Diagram

```
[Physical Printers]  ←→ [MQTT Broker] ←→ [Real-Time Processor]
       or                   ↑      ↓              ↓
[Data Synthesizer]          |  [Telegraf] → [InfluxDB] → [Grafana]
                            ↓      ↑
                    [Feedback Control]
```

### Technology Stack

| Component          | Technology          | Purpose                          |
|--------------------|---------------------|----------------------------------|
| MQTT Broker        | Mosquitto           | Message queuing                  |
| Data Pipeline      | Python + Telegraf   | Data collection/processing       |
| Time-Series DB     | InfluxDB 2.0        | Metrics storage                  |
| Visualization      | Grafana             | Dashboards & alerts              |
| ML Processing      | Scikit-learn        | Anomaly detection                |
| Containerization   | Docker              | Deployment management            |

## 🌊 Data Flow

1. **Data Generation**:
   - Physical printers or synthesizer publish JSON messages to:
     - `printing/<printer_id>/sensor`
   - Sample message:
     ```json
     {
       "printer_id": "printer_1",
       "timestamp": "2023-06-15T14:32:10Z",
       "layer_height": 0.2,
       "nozzle_temp": 215,
       "bed_temp": 60,
       "roughness": 32,
       "anomaly": null
     }
     ```

2. **Processing**:
   - Real-time processor:
     - Subscribes to sensor topics
     - Stores data in InfluxDB
     - Runs ML inference
     - Publishes feedback to `printer/control/<printer_id>`

3. **Feedback Loop**:
   ```mermaid
   sequenceDiagram
     Printer->>MQTT: Publish sensor data
     MQTT->>Processor: Forward message
     Processor->>InfluxDB: Store metrics
     Processor->>ML Model: Get prediction
     alt roughness > threshold
       Processor->>MQTT: Publish adjustment
       MQTT->>Printer: Receive new parameters
     end
   ```

## 🛠 Installation

### Prerequisites
- Docker 20.10+
- Docker Compose 2.12+
- Python 3.9+ (for development)

### Setup Steps

1. Clone repository:
   ```bash
   git clone https://github.com/yourrepo/3d-printing-mlops.git
   cd 3d-printing-mlops
   ```

2. Set up environment:
   ```bash
   cp .env.example .env
   nano .env  # Edit configuration
   ```

3. Initialize MQTT authentication:
   ```bash
   chmod +x scripts/init_mqtt.sh
   ./scripts/init_mqtt.sh
   ```

4. Start the system:
   ```bash
   docker-compose up -d --build
   ```

## ⚙ Configuration

### Key Environment Variables

| Variable                      | Default       | Description                     |
|-------------------------------|---------------|---------------------------------|
| `MQTT_USERNAME`               | mlops_user    | Broker authentication           |
| `MQTT_PASSWORD`               | -             | Broker authentication           |
| `ROUGHNESS_THRESHOLD`         | 75            | Quality control threshold       |
| `SYNTHESIZER_RATE_HZ`         | 100           | Messages per second             |
| `INFLUXDB_BUCKET`             | printing_metrics | Time-series storage bucket    |

### File Structure

```
.
├── config/
│   ├── mosquitto.conf          # MQTT broker config
│   └── telegraf.conf           # Metrics collection
├── data/
│   └── data.csv                # Sample dataset
├── dashboard/
│   └── provisioning/           # Grafana dashboards
├── scripts/
│   └── init_mqtt.sh            # Setup script
├── synthesizer/
│   ├── synthesizer.py          # Data generator
│   └── Dockerfile              # Container config
└── real-time-engine/
    ├── processor.py            # ML processor
    └── requirements.txt        # Python dependencies
```

## 🖥 Usage

### Accessing Services

| Service    | URL                  | Credentials           |
|------------|----------------------|-----------------------|
| Grafana    | http://localhost:3000 | admin/grafanapass    |
| InfluxDB   | http://localhost:8086 | admin/influxpass     |

### Common Operations

**View real-time metrics**:
```bash
docker-compose exec mqtt mosquitto_sub -t 'printing/#' -v
```

**Send test command**:
```bash
docker-compose exec mqtt mosquitto_pub -t 'printer/control/1' -m '{"speed":50}'
```

**Export metrics**:
```bash
docker-compose exec influxdb influx query -f /scripts/export.iql
```

## 🐛 Troubleshooting

### Common Issues

1. **MQTT Connection Failures**:
   - Verify pwfile permissions:
     ```bash
     chmod 600 config/pwfile
     ```
   - Check broker logs:
     ```bash
     docker-compose logs mqtt
     ```

2. **Missing Data in Grafana**:
   - Verify Telegraf connection:
     ```bash
     docker-compose exec telegraf telegraf --test
     ```

3. **High Resource Usage**:
   - Adjust synthesizer rate:
     ```bash
     docker-compose stop synthesizer
     docker-compose run -e BASE_RATE_HZ=20 synthesizer
     ```

## 🚀 Future Enhancements

1. **Machine Learning**:
   - Implement real DNN model
   - Add online learning

2. **Deployment**:
   - Kubernetes manifests
   - CI/CD pipeline

3. **Features**:
   - SMS/Email alerts
   - Print job scheduling
   - Material database

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

---

This documentation provides complete coverage of:
- System architecture and design decisions
- Detailed installation/configuration instructions
- Operational procedures
- Maintenance guidelines
- Future roadmap
