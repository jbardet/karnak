# Karnak Timing Analysis - Virtual Environment Setup

## 🐍 **Python Virtual Environment Created**

A dedicated Python virtual environment has been created for the Karnak timing analysis tools.

### **Environment Details**
- **Name**: `karnak_timing_env`
- **Location**: `C:\Users\james\Documents\karnak\karnak_timing_env\`
- **Python Version**: Python 3.13
- **Status**: ✅ Active and ready to use

### **Installed Libraries**
```
matplotlib      3.10.6  - For creating graphs and visualizations
pandas          2.3.2   - For data analysis and manipulation
numpy           2.3.3   - For numerical computations
contourpy       1.3.3   - Matplotlib dependency
cycler          1.4.9   - Matplotlib dependency
fonttools       4.60.0  - Matplotlib dependency
kiwisolver      1.4.9   - Matplotlib dependency
pillow          11.3.0  - Image processing
pyparsing       3.2.5   - Text parsing
python-dateutil 2.9.0   - Date/time utilities
pytz            2025.2  - Timezone support
tzdata          2025.2  - Timezone data
```

## 🚀 **How to Use the Virtual Environment**

### **Activate the Environment**
```bash
# Windows PowerShell/Command Prompt
karnak_timing_env\Scripts\activate

# Windows Git Bash
source karnak_timing_env/Scripts/activate

# Linux/Mac
source karnak_timing_env/bin/activate
```

### **Deactivate the Environment**
```bash
deactivate
```

### **Run Analysis Scripts**
```bash
# Extract timing logs
python extract_karnak_logs.py karnak --timing-only

# Analyze timing data
python karnak_timing_analyzer.py karnak_logs.txt --all

# Run automated analysis
python run_analysis.py
```

## 📁 **Environment Structure**
```
karnak_timing_env/
├── Scripts/
│   ├── activate.bat          # Windows activation script
│   ├── activate.ps1          # PowerShell activation script
│   ├── python.exe            # Python interpreter
│   ├── pip.exe               # Package installer
│   └── ...
├── Lib/
│   ├── site-packages/        # Installed packages
│   │   ├── matplotlib/
│   │   ├── pandas/
│   │   ├── numpy/
│   │   └── ...
│   └── ...
└── pyvenv.cfg                # Environment configuration
```

## 🔧 **Environment Management**

### **Update Packages**
```bash
# Activate environment first
karnak_timing_env\Scripts\activate

# Update all packages
pip install --upgrade pip
pip install --upgrade -r requirements.txt
```

### **Add New Packages**
```bash
# Activate environment
karnak_timing_env\Scripts\activate

# Install new package
pip install package_name

# Update requirements.txt
pip freeze > requirements.txt
```

### **Remove Environment**
```bash
# Deactivate first
deactivate

# Remove directory
rmdir /s karnak_timing_env
```

## ✅ **Verification**

The environment has been tested and verified to work with:
- ✅ Log extraction from Docker containers
- ✅ Timing data analysis and statistics
- ✅ Graph generation (6 different types)
- ✅ CSV and JSON data export
- ✅ Automated analysis workflows

## 🎯 **Benefits of Virtual Environment**

1. **Isolation**: Prevents conflicts with system Python packages
2. **Reproducibility**: Consistent environment across different machines
3. **Version Control**: Specific package versions for stability
4. **Clean Installation**: Only necessary packages installed
5. **Easy Management**: Simple activation/deactivation

## 📝 **Quick Start Commands**

```bash
# 1. Activate environment
karnak_timing_env\Scripts\activate

# 2. Extract logs
python extract_karnak_logs.py karnak --timing-only --timestamp

# 3. Run analysis
python karnak_timing_analyzer.py karnak_logs_*.txt --all

# 4. View results
# Check timing_analysis/ directory for graphs and data files
```

Your Python virtual environment is ready for Karnak timing analysis! 🎉
