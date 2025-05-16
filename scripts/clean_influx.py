from influxdb_client import InfluxDBClient
from datetime import datetime, timedelta

client = InfluxDBClient.from_env_properties()
delete_api = client.delete_api()

start = (datetime.now() - timedelta(days=90)).isoformat()
stop = (datetime.now() - timedelta(days=30)).isoformat()

delete_api.delete(start, stop, '_measurement="printing_events"', 
                 bucket="printing_events", org="3dprinting")
