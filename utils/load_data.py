# utils/load_data.py
import pandas as pd
from influxdb_client import InfluxDBClient

def load_historical_data():
    # Load CSV
    df = pd.read_csv('data/data.csv')
    
    # Connect to InfluxDB
    client = InfluxDBClient.from_env_properties()
    write_api = client.write_api()
    
    # Convert each row to Influx point
    for _, row in df.iterrows():
        point = Point("historical_prints") \
            .tag("material", row['material']) \
            .field("roughness", float(row['roughness'])) \
            .field("temperature", float(row['nozzle_temperature'])) \
            .time(datetime.utcnow())  # Or use actual timestamp if available
        
        write_api.write(
            bucket="printing_metrics",
            record=point)
    
    print(f"Loaded {len(df)} historical records")

if __name__ == "__main__":
    load_historical_data()
