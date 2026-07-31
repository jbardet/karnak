# DICOM Processing Timing Setup

This document explains how to set up and use the DICOM processing timing functionality in Karnak.

## Overview

Karnak now includes detailed timing measurements for DICOM file processing with three distinct phases:
1. **DICOM_READ**: Time to read and parse the incoming DICOM file
2. **KARNAK_PROCESS**: Time for Karnak to process the DICOM (anonymization, transformations, etc.)
3. **DICOM_WRITE**: Time to write the processed DICOM file to the destination

## Timing Implementation

### Key Components

1. **DicomProcessingTimer**: Utility class that tracks timing for each DICOM instance
2. **CStoreSCPService**: Initiates timing when DICOM files are received
3. **ForwardService**: Tracks detailed phase timing during processing
4. **Logging Configuration**: Dedicated timing logs for analysis

### Log Output Format

The timing logs include:
- Individual phase timing: `TIMING: [SOPInstanceUID] Starting/Completed phase PHASE_NAME`
- Final summary: `TIMING_SUMMARY: [SOPInstanceUID] Total: X.XX ms | DICOM_READ: X.XX ms | KARNAK_PROCESS: X.XX ms | DICOM_WRITE: X.XX ms`

## Docker Setup

### Using Docker Compose

1. Use the provided `docker/docker-compose-with-karnak.yml` configuration:

```bash
cd docker
docker-compose -f docker-compose-with-karnak.yml up -d
```

2. The configuration includes:
   - Volume mount for accessing timing logs: `./karnak-logs:/app/logs`
   - Proper environment variables for timing log configuration
   - Log rotation settings

### Accessing Timing Logs

#### Method 1: File-based Logs (Production)
```bash
# View timing logs in real-time
tail -f docker/karnak-logs/Timing/timing.log

# View all logs including timing
tail -f docker/karnak-logs/all/all.log | grep TIMING

# Search for specific DICOM instance timing
grep "1.2.3.4.5.6.7.8" docker/karnak-logs/Timing/timing.log
```

#### Method 2: Docker Logs (Development)
```bash
# View container logs with timing information
docker logs -f karnak-app | grep TIMING

# Filter for timing summaries only
docker logs karnak-app 2>&1 | grep "TIMING_SUMMARY"
```

### Log Analysis Examples

#### Extract Timing Summary for Analysis
```bash
# Extract all timing summaries to CSV format
grep "TIMING_SUMMARY" docker/karnak-logs/all/all.log | \
  sed -E 's/.*\[([^\]]+)\] Total: ([0-9.]+) ms.*DICOM_READ: ([0-9.]+) ms.*KARNAK_PROCESS: ([0-9.]+) ms.*DICOM_WRITE: ([0-9.]+) ms.*/\1,\2,\3,\4,\5/' > timing_analysis.csv

# View average processing times
awk -F',' 'NR>1 {total+=$2; read+=$3; process+=$4; write+=$5; count++} END {print "Avg Total:", total/count "ms"; print "Avg Read:", read/count "ms"; print "Avg Process:", process/count "ms"; print "Avg Write:", write/count "ms"}' timing_analysis.csv
```

#### Monitor Real-time Performance
```bash
# Monitor timing summaries in real-time
tail -f docker/karnak-logs/all/all.log | grep --line-buffered "TIMING_SUMMARY" | while read line; do
  echo "$(date): $line"
done
```

## Environment Variables

Configure timing log behavior with these environment variables:

```yaml
environment:
  # Timing log file size before rotation
  - KARNAK_TIMING_LOGS_MAX_FILE_SIZE=50MB
  
  # Number of timing log files to keep
  - KARNAK_TIMING_LOGS_MAX_INDEX=5
  
  # General log settings
  - KARNAK_LOGS_MAX_FILE_SIZE=100MB
  - KARNAK_LOGS_MAX_INDEX=10
```

## Development Setup

For development environments, timing logs are output to the console with the standard logging format.

### Enable Timing Logs in Development
Set the environment variable:
```bash
export ENVIRONMENT=DEV
```

Then start the application. Timing logs will appear in the console output.

## Troubleshooting

### No Timing Logs Appearing

1. Check log level configuration:
   ```bash
   # Ensure INFO level is enabled for timing logger
   grep -A 5 "DicomProcessingTimer" src/main/resources/logback.xml
   ```

2. Verify timing directory exists:
   ```bash
   ls -la docker/karnak-logs/Timing/
   ```

3. Check container logs for errors:
   ```bash
   docker logs karnak-app | grep -i error
   ```

### High Memory Usage

If timing contexts accumulate (due to errors), monitor with:
```bash
# Check active timing contexts in logs
docker logs karnak-app | grep "Active timing contexts"
```

The timer automatically cleans up contexts on completion or errors.

## Performance Impact

The timing functionality has minimal performance impact:
- Uses `System.nanoTime()` for high precision
- Minimal memory footprint per DICOM instance
- Automatic cleanup prevents memory leaks
- Log I/O is asynchronous and buffered

## Integration with Monitoring Systems

The structured timing logs can be easily integrated with monitoring systems:

### Prometheus/Grafana
Parse timing logs and expose metrics via a custom exporter.

### ELK Stack
Configure Logstash to parse timing logs and send to Elasticsearch for analysis.

### Example Logstash Configuration
```ruby
filter {
  if [message] =~ "TIMING_SUMMARY" {
    grok {
      match => { "message" => "TIMING_SUMMARY: \[%{DATA:sop_instance_uid}\] Total: %{NUMBER:total_ms:float} ms.*DICOM_READ: %{NUMBER:read_ms:float} ms.*KARNAK_PROCESS: %{NUMBER:process_ms:float} ms.*DICOM_WRITE: %{NUMBER:write_ms:float} ms" }
    }
    
    mutate {
      add_tag => ["timing_summary"]
    }
  }
}
```
