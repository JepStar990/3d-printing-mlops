# Running the 3D Printer Monitoring Project

This project uses Docker Compose to orchestrate all services.

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB of RAM available

## Quick Start

1. Ensure all environment files are present:
   - `real-time-engine/.env.real-time`
   - `synthesizer/.env.synthesizer`
   (They should already exist with default values; if not, copy the example from the respective directories.)

2. From the project root, run:
   ```bash
   docker-compose up -d
   ```
   Or use the convenience script:
   ```bash
   bash scripts/run.sh
   ```

3. Watch the logs (optional):
   ```bash
   docker-compose logs -f
   ```

4. Access the monitoring dashboards:
   - Grafana: http://localhost:3000 (default credentials admin/admin)
   - InfluxDB UI: http://localhost:8086

## Services started

- **synthesizer**: Generates synthetic 3D printer telemetry and publishes to MQTT.
- **real-time-engine**: Subscribes to MQTT, processes data with ML model, stores in InfluxDB, and sends feedback.
- **influxdb**: Time‑series database for storing metrics.
- **grafana**: Dashboard for visualizing printer health and roughness predictions.
- **mosquitto**: MQTT message broker (runs inside the `real-time-engine` container, not a separate service).

## ML Model Training

To train the ML model for surface roughness prediction and log experiments to DagsHub:

1. **Install dependencies** (if not already installed):
   ```bash
   pip install -r real-time-engine/requirements.txt
   ```

2. **Set up DagsHub**:
   - Create a repository on [DagsHub](https://dagshub.com).
   - Update `real-time-engine/.env.real-time` with your `DAGSHUB_REPO` URL, and optionally set `DAGSHUB_USERNAME` and `DAGSHUB_TOKEN` environment variables for authentication.

3. **Run the training script**:
   ```bash
   cd real-time-engine
   python3 train_model.py
   ```
   Alternatively, use the convenience script from the project root:
   ```bash
   bash scripts/train_model.sh
   ```
   The script loads historical data (via `utils.load_data`), trains a k‑nearest neighbors regressor (or other model specified by `MODEL_TYPE`), evaluates performance, logs metrics to DagsHub via MLflow, and saves the trained model locally (default path `models/model.pkl`).

4. **Use the trained model in the real‑time engine**:
   Ensure the `MODEL_PATH` environment variable points to the saved model file. The processor will load it automatically on startup.

## Stopping the project

```bash
docker-compose down
```

## Committing Changes

After making modifications, you can commit them with:

```bash
git add .
git commit -m "your descriptive message"
```

To set the author name and email, configure git beforehand:

```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## Troubleshooting

- If services fail to start, check that the required ports (1883, 8086, 3000) are free.
- Verify that the `.env` files contain correct MQTT broker address (should be `mosquitto` inside the Docker network).
- View logs for a specific service: `docker-compose logs synthesizer`
- Use `docker-compose ps` to see the status of each container.
