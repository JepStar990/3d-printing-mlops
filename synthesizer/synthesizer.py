import os
import json
import random
import time
import asyncio
import paho.mqtt.client as mqtt
from datetime import datetime
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Load environment
load_dotenv('.env')  # Load the main .env
load_dotenv('.env.synthesizer')  # Load the synthesizer-specific .env

class AnomalyGenerator:
    @staticmethod
    def inject_spike(data, field, magnitude=3):
        if random.random() < float(os.getenv('ANOMALY_PROBABILITY', 0.05)):
            data[field] *= magnitude
            data['anomaly'] = f'spike_{field}'
        return data

    @staticmethod
    def inject_drift(data, field, printer_id, state):
        key = f"{printer_id}_{field}"
        if key not in state['drifts']:
            if random.random() < 0.03:  # 3% chance to start drift
                state['drifts'][key] = {
                    'direction': random.choice([-1, 1]),
                    'duration': random.randint(10, 30)
                }
        
        if key in state['drifts']:
            drift = state['drifts'][key]
            data[field] *= 1 + (0.02 * drift['direction'])
            drift['duration'] -= 1
            if drift['duration'] <= 0:
                del state['drifts'][key]
            data['anomaly'] = f'drift_{field}'
        return data

class DataSynthesizer:
    def __init__(self):
        self.base_data = self.load_dataset()
        self.state = {
            'printers': {},
            'drifts': {},
            'feedback_rules': {
                'roughness': lambda x: x['print_speed'] * max(0.5, float(os.getenv('ADJUSTMENT_FACTOR', 0.8)))
            }
        }
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.setup_mqtt()

    def load_dataset(self):
        try:
            df = pd.read_csv('/app/data/data.csv')
            print(f"Loaded dataset with {len(df)} rows")
            return df.to_dict('records')
        except Exception as e:
            print(f"Error loading dataset: {e}")
            # Fallback to minimal data
            return [
                {'layer_height': 2.0, 'wall_thickness': 8, 'roughness': 25}
            ]

    def setup_mqtt(self):
        self.client.username_pw_set(
            os.getenv('MQTT_USERNAME'),
            os.getenv('MQTT_PASSWORD'))
        self.client.connect(os.getenv('MQTT_HOST', 'mqtt'), 1883)
        
        if os.getenv('FEEDBACK_ENABLED', 'true').lower() == 'true':
            self.client.on_message = self.on_feedback
            self.client.subscribe('printer/control/#')

    def on_feedback(self, client, userdata, message):
        try:
            feedback = json.loads(message.payload.decode())
            printer_id = feedback['printer_id']
            self.state['printers'][printer_id] = feedback
            print(f"Applied feedback to {printer_id}: {feedback}")
        except Exception as e:
            print(f"Feedback error: {e}")

    def generate_message(self, printer_id):
        # Initialize printer state if new
        if printer_id not in self.state['printers']:
            self.state['printers'][printer_id] = {
                'base_params': random.choice(self.base_data),
                'last_adjustment': None
            }

        # Get base parameters
        printer_state = self.state['printers'][printer_id]
        msg = printer_state['base_params'].copy()
        
        # Convert to dict if pandas Series
        if hasattr(msg, 'to_dict'):
            msg = msg.to_dict()

        # Add normal variation
        for key in msg:
            if isinstance(msg[key], (int, float)):
                msg[key] *= random.uniform(0.95, 1.05)
                msg[key] = round(msg[key], 2)

        # Inject anomalies
        msg = AnomalyGenerator.inject_spike(msg, 'nozzle_temperature')
        msg = AnomalyGenerator.inject_drift(msg, 'bed_temperature', printer_id, self.state)

        # Apply feedback if any
        if 'last_adjustment' in printer_state and printer_state['last_adjustment']:
            for param, value in printer_state['last_adjustment'].items():
                if param in msg:
                    msg[param] = value

        # Add metadata
        msg.update({
            'timestamp': datetime.utcnow().isoformat(),
            'printer_id': printer_id,
            'cycle_count': printer_state.get('cycle_count', 0)
        })

        # Update state
        printer_state['cycle_count'] = printer_state.get('cycle_count', 0) + 1
        return msg

    async def run(self):
        printer_count = int(os.getenv('PRINTER_COUNT', 3))
        rate_hz = int(os.getenv('BASE_RATE_HZ', 100))
        delay = 1.0 / rate_hz
        
        self.client.loop_start()
        
        try:
            while True:
                start_time = time.time()
                
                # Generate messages for all printers
                for printer_id in range(1, printer_count + 1):
                    msg = self.generate_message(f'printer_{printer_id}')
                    self.client.publish(
                        f'printing/{printer_id}/sensor',
                        json.dumps(msg),
                        qos=1)
                
                # Sleep for remaining time to maintain rate
                elapsed = time.time() - start_time
                await asyncio.sleep(max(0, delay - elapsed))
                
        except KeyboardInterrupt:
            self.client.loop_stop()

if __name__ == "__main__":
    # Initialize with automatic dataset loading
    synthesizer = DataSynthesizer()

    try:
        # Start the synthetic data generation
        asyncio.run(synthesizer.run())
    except KeyboardInterrupt:
        print("\nGracefully shutting down synthesizer...")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        # Cleanup MQTT connection
        if hasattr(synthesizer, 'client'):
            synthesizer.client.disconnect()
        print("Synthesizer stopped")
