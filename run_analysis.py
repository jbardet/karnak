#!/usr/bin/env python3
"""
Automated Karnak Timing Analysis

This script automates the complete workflow of extracting logs and analyzing timing data.
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"STEP: {description}")
    print(f"COMMAND: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("SUCCESS")
        if result.stdout:
            print("OUTPUT:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("ERROR:", e)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except FileNotFoundError:
        print("ERROR: Command not found")
        return False

def main():
    print("KARNAK TIMING ANALYSIS AUTOMATION")
    print("="*60)
    
    # Configuration
    container_name = 'karnak'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'karnak_timing_logs_{timestamp}.txt'
    analysis_dir = f'timing_analysis_{timestamp}'
    
    print(f"Container: {container_name}")
    print(f"Log file: {log_file}")
    print(f"Analysis dir: {analysis_dir}")
    
    # Step 1: Check if container is running
    if not run_command(['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}'], 
                      "Checking if Karnak container is running"):
        print("ERROR: Karnak container is not running!")
        print("Please start it with: docker-compose -f docker-compose-timing.yml up -d")
        sys.exit(1)
    
    # Step 2: Extract timing logs
    if not run_command(['python', 'extract_karnak_logs.py', container_name, '--timing-only', '--output', log_file], 
                      "Extracting timing logs from Docker"):
        print("ERROR: Failed to extract logs")
        sys.exit(1)
    
    # Step 3: Check if log file has content
    if not Path(log_file).exists() or Path(log_file).stat().st_size == 0:
        print("ERROR: No timing data found in logs!")
        print("Make sure DICOM files are being processed through Karnak")
        sys.exit(1)
    
    # Step 4: Run timing analysis
    if not run_command(['python', 'karnak_timing_analyzer.py', log_file, '--all', '--output-dir', analysis_dir], 
                      "Running timing analysis"):
        print("ERROR: Failed to analyze timing data")
        sys.exit(1)
    
    # Step 5: Show results
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE!")
    print('='*60)
    print(f"Log file: {Path(log_file).absolute()}")
    print(f"Analysis directory: {Path(analysis_dir).absolute()}")
    
    # List generated files
    analysis_path = Path(analysis_dir)
    if analysis_path.exists():
        print("\nGenerated files:")
        for file in sorted(analysis_path.iterdir()):
            if file.is_file():
                size = file.stat().st_size
                print(f"  {file.name} ({size:,} bytes)")
    
    print(f"\nTo view graphs, open the files in: {analysis_path.absolute()}")
    print("To run analysis again, use:")
    print(f"  python karnak_timing_analyzer.py {log_file} --all")

if __name__ == '__main__':
    main()
