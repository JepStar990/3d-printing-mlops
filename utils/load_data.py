# utils/load_data.py
import pandas as pd
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.domain.write_precision import WritePrecision
from datetime import datetime
import os

def load_historical_data():
    """
    Load historical data for training.
    First tries to load from CSV, if not found, tries to query from InfluxDB.
    If neither works, generates synthetic data for demonstration.
    Returns a pandas DataFrame with features and target.
    """
    # Try to load from CSV first
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'data.csv')
    
    if os.path.exists(csv_path):
        print(f"Loading data from CSV: {csv_path}")
        df = pd.read_csv(csv_path)
    else:
        print("CSV file not found. Attempting to query data from InfluxDB...")
        # Try to fetch data from InfluxDB
        try:
            df = query_influxdb_data()
            if df is not None and not df.empty:
                print(f"Successfully queried {len(df)} records from InfluxDB")
                # Save to CSV for future use
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                df.to_csv(csv_path, index=False)
                print(f"Saved data to {csv_path}")
            else:
                print("No data in InfluxDB. Generating synthetic data...")
                df = generate_synthetic_data()
        except Exception as e:
            print(f"Error querying InfluxDB: {e}. Generating synthetic data...")
            df = generate_synthetic_data()
    
    print(f"Loaded {len(df)} historical records")
    
    # Rename columns to match expected names in train_model.py
    # The training script expects 'surface_roughness' as target column
    # Also ensure other columns have consistent names
    column_mapping = {
        'roughness': 'surface_roughness',
        'surface_roughness': 'surface_roughness',  # In case it's already named correctly
    }
    
    # Apply renaming
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df = df.rename(columns={old_name: new_name})
    
    # If 'surface_roughness' is still not present, check for similar columns
    if 'surface_roughness' not in df.columns:
        # Look for any column containing 'roughness'
        roughness_cols = [col for col in df.columns if 'roughness' in col.lower()]
        if roughness_cols:
            df = df.rename(columns={roughness_cols[0]: 'surface_roughness'})
    
    return df

def query_influxdb_data():
    """
    Query historical data from InfluxDB.
    Returns a pandas DataFrame or None if query fails.
    """
    try:
        from influxdb_client import InfluxDBClient
        from influxdb_client.client.query_api import QueryApi
        
        client = InfluxDBClient.from_env_properties()
        query_api = client.query_api()
        
        # Query to get historical print data
        query = '''
        from(bucket: "printing_metrics")
          |> range(start: -30d)
          |> filter(fn: (r) => r._measurement == "historical_prints")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        result = query_api.query_data_frame(query)
        
        if result is not None and not result.empty:
            # Rename columns to match expected format
            # The exact column names depend on your data structure
            # This is a generic approach
            df = pd.DataFrame(result)
            # Ensure we have required columns
            required_cols = ['material', 'roughness', 'nozzle_temperature']
            # Check which columns are present and rename if needed
            return df
        else:
            return None
    except Exception:
        return None

def generate_synthetic_data(num_samples=1000):
    """
    Generate synthetic training data for demonstration.
    """
    import numpy as np
    
    np.random.seed(42)
    
    materials = ['PLA', 'ABS', 'PETG', 'TPU']
    
    data = {
        'material': np.random.choice(materials, num_samples),
        'nozzle_temperature': np.random.uniform(180, 250, num_samples),
        'bed_temperature': np.random.uniform(50, 100, num_samples),
        'print_speed': np.random.uniform(30, 100, num_samples),
        'layer_height': np.random.uniform(0.1, 0.3, num_samples),
        'surface_roughness': np.random.uniform(10, 100, num_samples)  # Target variable
    }
    
    # Add some correlation between features and roughness
    # Higher temperature and lower speed tend to reduce roughness
    data['surface_roughness'] = (
        100 
        - 0.3 * (data['nozzle_temperature'] - 180) 
        + 0.2 * data['print_speed']
        + np.random.normal(0, 10, num_samples)
    )
    # Ensure roughness is within bounds
    data['surface_roughness'] = np.clip(data['surface_roughness'], 10, 100)
    
    df = pd.DataFrame(data)
    return df

if __name__ == "__main__":
    load_historical_data()
