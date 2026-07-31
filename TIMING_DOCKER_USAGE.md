# Running Karnak with Timing Measurements

This guide shows how to run the timing-enabled Karnak container using your existing docker-compose setup.

## Quick Start

1. **Use the updated docker-compose file:**
   ```bash
   cd docker
   docker-compose -f docker-compose-with-karnak.yml up -d
   ```

2. **Verify the containers are running:**
   ```bash
   docker ps
   ```
   You should see: `karnak`, `karnak-cache`, and `karnak-db` containers.

3. **Check timing logs in real-time:**
   ```bash
   # View timing logs directly from the container
   docker logs -f karnak | grep TIMING
   
   # Or view from the mounted log files
   tail -f docker/karnak-logs/Timing/timing.log
   ```

## Key Changes from Original Setup

### Docker Image
- **Original:** `osirixfoundation/karnak:master`
- **Timing-enabled:** `osirixfoundation/karnak:timing`

### Added Volume Mount
```yaml
volumes:
  - ./karnak-logs:/app/logs  # Access timing logs from host
```

### Added Environment Variables
```yaml
environment:
  # Timing log configuration
  KARNAK_TIMING_LOGS_MAX_FILE_SIZE: 50MB
  KARNAK_TIMING_LOGS_MAX_INDEX: 5
  KARNAK_LOGS_MAX_FILE_SIZE: 100MB
  KARNAK_LOGS_MAX_INDEX: 10
```

## Viewing Timing Information

### 1. Real-time Container Logs
```bash
# All timing information
docker logs -f karnak | grep TIMING

# Only timing summaries
docker logs karnak 2>&1 | grep "TIMING_SUMMARY"
```

### 2. Log Files (via mounted volume)
```bash
# Create log directory if it doesn't exist
mkdir -p docker/karnak-logs

# View timing logs
tail -f docker/karnak-logs/Timing/timing.log

# View all logs (includes timing)
tail -f docker/karnak-logs/all/all.log | grep TIMING
```

### 3. Log Format Examples

**Individual Phase Timing:**
```
2025-09-29 16:30:45.123 [thread] INFO  o.k.b.u.DicomProcessingTimer - TIMING: [1.2.3.4.5] Starting phase DICOM_READ at 1727627445123
2025-09-29 16:30:45.145 [thread] INFO  o.k.b.u.DicomProcessingTimer - TIMING: [1.2.3.4.5] Completed phase DICOM_READ in 22.34 ms
```

**Final Summary:**
```
2025-09-29 16:30:45.267 [thread] INFO  o.k.b.u.DicomProcessingTimer - TIMING_SUMMARY: [1.2.3.4.5] Total: 144.23 ms | DICOM_READ: 22.34 ms | KARNAK_PROCESS: 98.45 ms | DICOM_WRITE: 23.44 ms
```

## Performance Analysis

### Extract Timing Data for Analysis
```bash
# Extract timing summaries to CSV
grep "TIMING_SUMMARY" docker/karnak-logs/all/all.log | \
  sed -E 's/.*\[([^\]]+)\] Total: ([0-9.]+) ms.*DICOM_READ: ([0-9.]+) ms.*KARNAK_PROCESS: ([0-9.]+) ms.*DICOM_WRITE: ([0-9.]+) ms.*/\1,\2,\3,\4,\5/' > timing_analysis.csv

echo "SOP_Instance_UID,Total_ms,Read_ms,Process_ms,Write_ms" | cat - timing_analysis.csv > timing_analysis_with_header.csv
```

### Calculate Average Processing Times
```bash
# Calculate averages (excluding header)
awk -F',' 'NR>1 {total+=$2; read+=$3; process+=$4; write+=$5; count++} 
END {
  print "Average Total:", total/count "ms"
  print "Average Read:", read/count "ms" 
  print "Average Process:", process/count "ms"
  print "Average Write:", write/count "ms"
}' timing_analysis_with_header.csv
```

## Configuration Details

### Ports
- **8080:8081** - Web interface (mapped to host port 8080)
- **11119:11119** - DICOM listener port

### Volumes
- `./processed-dicoms:/app/archive` - DICOM archive storage
- `./karnak-logs:/app/logs` - Log files (including timing logs)

### Networks
- `karnak-data` - Internal communication between services
- `karnak-network` - External network access

## Troubleshooting

### No Timing Logs Appearing
1. Check if container is running: `docker ps | grep karnak`
2. Check container logs: `docker logs karnak`
3. Verify log directory exists: `ls -la docker/karnak-logs/`
4. Check environment variables: `docker exec karnak env | grep TIMING`

### High Memory Usage
Monitor timing contexts: `docker logs karnak | grep "Active timing contexts"`

### Log Rotation Issues
Check disk space: `df -h docker/karnak-logs/`

## Stopping and Cleanup

```bash
# Stop containers
docker-compose -f docker-compose-with-karnak.yml down

# Remove volumes (WARNING: This deletes all data)
docker-compose -f docker-compose-with-karnak.yml down -v

# Clean up timing logs
rm -rf docker/karnak-logs/
```

## Integration with Monitoring

The structured timing logs can be easily integrated with monitoring systems:

### With ELK Stack
```bash
# Example logstash filter for timing summaries
filter {
  if [message] =~ "TIMING_SUMMARY" {
    grok {
      match => { 
        "message" => "TIMING_SUMMARY: \[%{DATA:sop_instance_uid}\] Total: %{NUMBER:total_ms:float} ms.*DICOM_READ: %{NUMBER:read_ms:float} ms.*KARNAK_PROCESS: %{NUMBER:process_ms:float} ms.*DICOM_WRITE: %{NUMBER:write_ms:float} ms" 
      }
    }
  }
}
```

### With Prometheus
Export metrics via a custom script that parses the timing logs and exposes them as Prometheus metrics.

## Next Steps

1. Send some DICOM files to port 11119 to test timing measurements
2. Monitor the logs to see timing information
3. Set up log rotation if needed for production use
4. Consider integrating with your monitoring infrastructure
