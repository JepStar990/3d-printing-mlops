#!/bin/bash
docker exec -it influxdb \
  influxd backup -portable \
  -db printing_metrics \
  /var/lib/influxdb2/backup/$(date +%Y%m%d)
