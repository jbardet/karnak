# Karnak DICOM Processing Timing Analysis - Complete Solution

## 🎯 **Mission Accomplished!**

You now have a complete solution for timing DICOM file processing through Karnak and analyzing the results. Here's what we've built:

## 📁 **Files Created**

### **Core Analysis Scripts**
- `karnak_timing_analyzer.py` - Main analysis script with comprehensive timing analysis
- `extract_karnak_logs.py` - Docker log extraction utility
- `run_analysis.py` - Automated analysis workflow
- `analyze_karnak_timing.ps1` - PowerShell script for Windows users

### **Configuration Files**
- `requirements.txt` - Python dependencies
- `TIMING_ANALYSIS_GUIDE.md` - Complete usage guide

### **Docker Configuration**
- `docker-compose-timing.yml` - Timing-enabled Karnak setup
- `docker/karnak.env` - Environment configuration with logging settings

## 🚀 **Quick Start Commands**

### **1. Extract Timing Logs**
```bash
# Extract all timing logs
python extract_karnak_logs.py karnak --timing-only

# Extract with timestamp
python extract_karnak_logs.py karnak --timing-only --timestamp

# Follow logs in real-time
python extract_karnak_logs.py karnak --follow --timing-only
```

### **2. Analyze Timing Data**
```bash
# Complete analysis (graphs + stats + data export)
python karnak_timing_analyzer.py karnak_logs.txt --all

# Generate only graphs
python karnak_timing_analyzer.py karnak_logs.txt --graphs

# Print statistics only
python karnak_timing_analyzer.py karnak_logs.txt --stats
```

### **3. Automated Workflow**
```bash
# Run complete automated analysis
python run_analysis.py

# PowerShell version (Windows)
.\analyze_karnak_timing.ps1
```

## 📊 **Analysis Outputs**

### **Generated Files**
- **CSV Data**: `timing_data_summary.csv` - Structured timing data
- **JSON Data**: `timing_data.json` - Complete timing data with metadata
- **Graphs**: 6 different visualization types:
  - `total_time_distribution.png` - Processing time histogram
  - `phase_comparison_boxplot.png` - Phase comparison
  - `time_series.png` - Processing time over time
  - `phase_pie_chart.png` - Phase time distribution
  - `cumulative_distribution.png` - CDF analysis
  - `correlation_heatmap.png` - Phase correlations

### **Sample Analysis Results**
```
KARNAK DICOM PROCESSING TIMING ANALYSIS
============================================================
Total files processed: 2
Analysis timestamp: 2025-09-29 20:55:32

OVERALL PROCESSING TIME STATISTICS:
----------------------------------------
Average: 3.00 ms
Median:  3.00 ms
Min:     2.34 ms
Max:     3.67 ms
Std Dev: 0.94 ms

AVERAGE TIME BY PHASE:
----------------------------------------
DICOM_READ:    0.62 ms (20.6%)
KARNAK_PROCESS: 0.70 ms (23.5%)
DICOM_WRITE:   1.16 ms (38.6%)
```

## 🔧 **Technical Implementation**

### **Timing Integration**
- **DicomProcessingTimer.java** - Core timing utility class
- **CStoreSCPService.java** - DICOM reception timing
- **ForwardService.java** - Processing and forwarding timing
- **Logback configuration** - Dedicated timing log appender

### **Docker Setup**
- **Timing-enabled image**: `osirixfoundation/karnak:timing`
- **Environment variables**: Logging level configuration
- **Volume mounts**: Log file access
- **Service dependencies**: Database and Redis

## 📈 **Real-Time Monitoring**

### **Live Log Monitoring**
```bash
# Terminal 1: Follow Docker logs
docker logs -f karnak | findstr TIMING

# Terminal 2: Extract and analyze
python extract_karnak_logs.py karnak --follow --timing-only
```

### **Continuous Analysis**
```bash
# Monitor and analyze every 5 minutes
while true; do
  python extract_karnak_logs.py karnak --timing-only --lines 100
  python karnak_timing_analyzer.py karnak_logs.txt --stats
  sleep 300
done
```

## 🎨 **Graph Types Generated**

1. **Distribution Analysis**: Histogram showing processing time distribution
2. **Phase Comparison**: Box plots comparing DICOM_READ, KARNAK_PROCESS, DICOM_WRITE
3. **Time Series**: Processing time trends over time
4. **Phase Breakdown**: Pie chart showing time distribution by phase
5. **Cumulative Distribution**: CDF for performance analysis
6. **Correlation Matrix**: Heatmap showing phase timing correlations

## 🔍 **Log Format**

The system captures timing in this format:
```
TIMING: [SOPInstanceUID] Starting phase DICOM_READ at timestamp
TIMING: [SOPInstanceUID] Completed phase DICOM_READ in X.XX ms
TIMING: [SOPInstanceUID] Starting phase KARNAK_PROCESS at timestamp
TIMING: [SOPInstanceUID] Completed phase KARNAK_PROCESS in X.XX ms
TIMING: [SOPInstanceUID] Starting phase DICOM_WRITE at timestamp
TIMING: [SOPInstanceUID] Completed phase DICOM_WRITE in X.XX ms
TIMING_SUMMARY: [SOPInstanceUID] Total: X.XX ms | DICOM_READ: X.XX ms | KARNAK_PROCESS: X.XX ms | DICOM_WRITE: X.XX ms
```

## 🏆 **Success Metrics**

✅ **Timing Integration**: Successfully integrated timing into Karnak processing pipeline  
✅ **Docker Container**: Timing-enabled Karnak container running successfully  
✅ **Log Extraction**: Automated log extraction from Docker containers  
✅ **Data Analysis**: Comprehensive timing analysis with statistics  
✅ **Visualization**: Multiple graph types for different analysis perspectives  
✅ **Automation**: Automated workflows for continuous monitoring  
✅ **Cross-Platform**: Works on Windows (PowerShell) and Linux/Mac  

## 🚀 **Next Steps**

1. **Process more DICOM files** to gather more timing data
2. **Set up continuous monitoring** using the automated scripts
3. **Analyze performance trends** over time
4. **Optimize bottlenecks** identified through timing analysis
5. **Create alerts** for performance degradation

## 📞 **Usage Examples**

### **Daily Analysis Workflow**
```bash
# Morning: Extract overnight logs
python extract_karnak_logs.py karnak --timing-only --timestamp

# Analyze performance
python karnak_timing_analyzer.py karnak_logs_20250129_080000.txt --all

# Review graphs in timing_analysis/ directory
```

### **Performance Monitoring**
```bash
# Monitor real-time performance
python extract_karnak_logs.py karnak --follow --timing-only --output live_monitor.txt

# In another terminal: Analyze every 10 minutes
watch -n 600 "python karnak_timing_analyzer.py live_monitor.txt --stats"
```

---

**🎉 Congratulations! You now have a complete DICOM processing timing analysis solution!**

The system successfully:
- Times each phase of DICOM processing (Read → Process → Write)
- Extracts timing data from Docker logs
- Generates comprehensive analysis reports
- Creates multiple visualization types
- Provides automated workflows for continuous monitoring

Your Karnak timing analysis system is ready for production use! 🚀
