import os
import json
import time
import random
import pickle
import paho.mqtt.client as mqtt
from datetime import datetime
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

# Load environment
load_dotenv('.env')  # Load the main .env
load_dotenv('.env.real-time')  # Load the real-time specific env

class RealTimeProcessor:
    def __init__(self):
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        
        self.setup_mqtt()
        self.setup_influxdb()
        self.model = self.load_model()
        self.threshold = float(os.getenv('ROUGHNESS_THRESHOLD', 75))
        self.adjustment_factor = float(os.getenv('ADJUSTMENT_FACTOR', 0.8))

    def setup_mqtt(self):
        max_retries = 5
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                self.client.username_pw_set(
                    os.getenv('MQTT_USERNAME'),
                    os.getenv('MQTT_PASSWORD'))
                self.client.connect(os.getenv('MQTT_HOST', 'mqtt'), 1883)
                print(" Successfully connected to MQTT broker")
                return
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"onnection attempt {attempt + 1} failed, retrying...")
                time.sleep(retry_delay)

    def setup_influxdb(self):
        self.influx_client = InfluxDBClient(
            url=f"http://{os.getenv('INFLUXDB_HOST', 'influxdb')}:8086",
            token=os.getenv('DOCKER_INFLUXDB_INIT_ADMIN_TOKEN'),
            org=os.getenv('INFLUXDB_ORG'))
        self.write_api = self.influx_client.write_api(write_options=SYNCHRONOUS)
        print(" InfluxDB client initialized")

    def load_model(self):
        model_path = os.getenv('MODEL_PATH')
        if model_path and os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    model, scaler, feature_names = pickle.load(f)
                    print(f" Loaded trained model from {model_path}")
                    return TrainedSklearnModel(model, scaler, feature_names)
            except Exception as e:
                print(f" Failed to load trained model: {e}. Using dummy model.")
        # Fallback to dummy model
        model_type = os.getenv('MODEL_TYPE', 'kNN')
        print(f" Loaded {model_type} model (dummy implementation)")
        return DummyModel()

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"MQTT Connected with result code {reason_code}")
        client.subscribe('printing/+/sensor')

    def on_message(self, client, userdata, message):
        try:
            data = json.loads(message.payload.decode())
            self.process_message(data)
        except Exception as e:
            print(f" Processing error: {e}")

    def process_message(self, data):
        try:
            # 1. Store in InfluxDB
            self.store_in_influx(data)
            
            # 2. Run ML prediction
            prediction = self.model.predict(data)
            
            # 3. Check thresholds and send feedback
            if data.get('roughness', 0) > self.threshold:
                self.send_feedback(data, prediction)
        except Exception as e:
            print(f"Message processing failed: {e}")

    def store_in_influx(self, data):
        point = Point("printing_metrics") \
            .tag("printer_id", data['printer_id']) \
            .field("roughness", float(data['roughness'])) \
            .field("temperature", float(data['nozzle_temperature'])) \
            .time(datetime.utcnow())

        self.write_api.write(
            bucket=os.getenv('INFLUX_BUCKET', 'printing_metrics'),
            org=os.getenv('INFLUXDB_ORG'),
            record=point)

    def send_feedback(self, data, prediction):
        adjustment = {
            'printer_id': data['printer_id'],
            'timestamp': datetime.utcnow().isoformat(),
            'original_speed': data['print_speed'],
            'new_speed': max(10, data['print_speed'] * self.adjustment_factor),  # Ensure minimum speed
            'reason': f"roughness_threshold_exceeded_{self.threshold}",
            'prediction': prediction
        }

        self.client.publish(
            f"printer/control/{data['printer_id']}",
            json.dumps(adjustment),
            qos=1)

        print(f"Sent adjustment for {data['printer_id']}: {adjustment}")

    def run(self):
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            print("\nGracefully shutting down...")
        finally:
            self.client.disconnect()
            if hasattr(self, 'influx_client'):
                self.influx_client.close()

class TrainedSklearnModel:
    """Wrapper for a scikit-learn model trained offline"""
    def __init__(self, model, scaler, feature_names):
        self.model = model
        self.scaler = scaler
        self.feature_names = feature_names

    def predict(self, data):
        # Build feature vector in same order as feature_names
        X = []
        for f in self.feature_names:
            # Use default 0 if feature missing
            X.append(data.get(f, 0.0))
        X_scaled = self.scaler.transform([X])[0]
        pred = self.model.predict([X_scaled])[0]
        return {
            'predicted_roughness': pred,
            'confidence': 0.95,   # could be derived from model uncertainty if available
            'anomaly_score': 0.0  # placeholder
        }

class DummyModel:
    """Placeholder for actual ML model"""
    def predict(self, data):
        return {
            'predicted_roughness': data['roughness'] * random.uniform(0.9, 1.1),
            'confidence': random.uniform(0.7, 0.95),
            'anomaly_score': random.uniform(0, 0.2)  # Added anomaly detection placeholder
        }

if __name__ == "__main__":
    print("Starting Real-Time Processor")
    try:
        processor = RealTimeProcessor()
        processor.run()
    except Exception as e:
        print(f"Critical error: {str(e)}")
        exit(1)
