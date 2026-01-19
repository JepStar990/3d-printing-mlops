# utils/load_data.py
import pandas as pd
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.write_precision import WritePrecision
from datetime import datetime
import os

def load_historical_data():
    # Load CSV - adjust path to be relative to project root
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'data.csv')
    df = pd.read_csv(csv_path)
    
    # Connect to InfluxDB
    client = InfluxDBClient.from_env_properties()
    write_api = client.write_api(write_options=SYNCHRONOUS)
    
    # Convert each row to Influx point
    for _, row in df.iterrows():
        # Create point using influxdb_client's Point class
        from influxdb_client import Point
        point = Point("historical_prints") \
            .tag("material", str(row['material'])) \
            .field("roughness", float(row['roughness'])) \
            .field("temperature", float(row['nozzle_temperature'])) \
            .time(datetime.utcnow(), WritePrecision.NS)  # Use current time if no timestamp
        
        write_api.write(
            bucket="printing_metrics",
            record=point)
    
    print(f"Loaded {len(df)} historical records")

if __name__ == "__main__":
    load_historical_data()
