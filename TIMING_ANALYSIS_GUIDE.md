# Karnak Timing Analysis Tools

This directory contains Python scripts to extract and analyze Karnak DICOM processing timing data from Docker logs.

## Files

- `extract_karnak_logs.py` - Extract logs from Docker container
- `karnak_timing_analyzer.py` - Analyze timing data and generate graphs
- `requirements.txt` - Python dependencies
- `run_analysis.py` - Automated analysis script

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Extract Logs from Docker

```bash
# Extract all logs
python extract_karnak_logs.py karnak

# Extract only timing logs
python extract_karnak_logs.py karnak --timing-only

# Extract last 1000 lines
python extract_karnak_logs.py karnak --lines 1000

# Follow logs in real-time
python extract_karnak_logs.py karnak --follow
```

### 3. Analyze Timing Data

```bash
# Run complete analysis
python karnak_timing_analyzer.py karnak_logs.txt --all

# Generate only graphs
python karnak_timing_analyzer.py karnak_logs.txt --graphs

# Print statistics only
python karnak_timing_analyzer.py karnak_logs.txt --stats
```

## Detailed Usage

### Extract Logs Script (`extract_karnak_logs.py`)

```bash
python extract_karnak_logs.py [CONTAINER_NAME] [OPTIONS]

Options:
  --output, -o FILE     Output file name (default: karnak_logs.txt)
  --timing-only, -t     Extract only timing-related logs
  --lines, -n NUMBER   Number of lines to extract (default: all)
  --follow, -f          Follow logs in real-time
  --timestamp           Add timestamp to output filename
```

**Examples:**
```bash
# Extract all logs from karnak container
python extract_karnak_logs.py karnak

# Extract only timing logs with timestamp
python extract_karnak_logs.py karnak --timing-only --timestamp

# Follow logs and save to custom file
python extract_karnak_logs.py karnak --follow --output live_logs.txt

# Extract last 500 lines of timing data
python extract_karnak_logs.py karnak --timing-only --lines 500
```

### Analysis Script (`karnak_timing_analyzer.py`)

```bash
python karnak_timing_analyzer.py LOG_FILE [OPTIONS]

Options:
  --output-dir DIR      Output directory (default: timing_analysis)
  --csv                 Save data to CSV files
  --json                Save data to JSON file
  --graphs              Generate timing graphs
  --stats               Print statistics report
  --all                 Run all analysis options
```

**Examples:**
```bash
# Complete analysis with all outputs
python karnak_timing_analyzer.py karnak_logs.txt --all

# Generate only graphs
python karnak_timing_analyzer.py karnak_logs.txt --graphs --output-dir graphs

# Save data in multiple formats
python karnak_timing_analyzer.py karnak_logs.txt --csv --json --stats

# Custom output directory
python karnak_timing_analyzer.py karnak_logs.txt --all --output-dir my_analysis
```

## Output Files

### CSV Files
- `timing_data_summary.csv` - Summary timing data for each file
- `timing_data_phases.csv` - Individual phase timing data

### JSON File
- `timing_data.json` - Complete timing data in JSON format

### Graphs (PNG files)
- `total_time_distribution.png` - Histogram of total processing times
- `phase_comparison_boxplot.png` - Box plot comparing phases
- `time_series.png` - Processing time over time
- `phase_pie_chart.png` - Pie chart of phase time distribution
- `cumulative_distribution.png` - Cumulative distribution function
- `correlation_heatmap.png` - Correlation matrix between phases

## Sample Workflow

1. **Start Karnak container:**
   ```bash
   docker-compose -f docker-compose-timing.yml up -d
   ```

2. **Process some DICOM files** (send files to Karnak)

3. **Extract timing logs:**
   ```bash
   python extract_karnak_logs.py karnak --timing-only --timestamp
   ```

4. **Run complete analysis:**
   ```bash
   python karnak_timing_analyzer.py karnak_logs_20250129_143022.txt --all
   ```

5. **View results:**
   - Check `timing_analysis/` directory for graphs
   - Review CSV files for detailed data
   - Check console output for statistics

## Real-time Monitoring

To monitor timing in real-time:

```bash
# Terminal 1: Follow logs
python extract_karnak_logs.py karnak --follow --timing-only --output live_timing.txt

# Terminal 2: Monitor Docker logs directly
docker logs -f karnak | findstr TIMING
```

## Troubleshooting

### No timing data found
- Ensure Karnak container is running with timing-enabled image
- Check that DICOM files are being processed
- Verify logging level is set to INFO or DEBUG

### Missing dependencies
```bash
pip install matplotlib pandas numpy
```

### Docker not found
- Ensure Docker is installed and running
- Check container name is correct
- Verify container is running: `docker ps`

## Log Format

The scripts expect logs in this format:
```
TIMING: [SOPInstanceUID] Starting phase DICOM_READ at timestamp
TIMING: [SOPInstanceUID] Completed phase DICOM_READ in X.XX ms
TIMING: [SOPInstanceUID] Starting phase KARNAK_PROCESS at timestamp
TIMING: [SOPInstanceUID] Completed phase KARNAK_PROCESS in X.XX ms
TIMING: [SOPInstanceUID] Starting phase DICOM_WRITE at timestamp
TIMING: [SOPInstanceUID] Completed phase DICOM_WRITE in X.XX ms
TIMING_SUMMARY: [SOPInstanceUID] Total: X.XX ms | DICOM_READ: X.XX ms | KARNAK_PROCESS: X.XX ms | DICOM_WRITE: X.XX ms
```
