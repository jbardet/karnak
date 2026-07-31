#!/usr/bin/env python3
"""
Docker Log Extractor for Karnak Timing Analysis

This script extracts Karnak timing logs from Docker and saves them to files.
"""

import subprocess
import argparse
import sys
from datetime import datetime
from pathlib import Path

def extract_docker_logs(container_name, output_file, lines=None, follow=False):
    """Extract logs from Docker container."""
    print(f"Extracting logs from container: {container_name}")
    
    # Build docker logs command
    cmd = ['docker', 'logs']
    
    if lines:
        cmd.extend(['--tail', str(lines)])
    
    if follow:
        cmd.append('-f')
    
    cmd.append(container_name)
    
    try:
        if follow:
            print(f"Following logs and saving to: {output_file}")
            print("Press Ctrl+C to stop...")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                        universal_newlines=True, bufsize=1)
                
                try:
                    for line in iter(process.stdout.readline, ''):
                        f.write(line)
                        f.flush()
                        print(line.rstrip())
                except KeyboardInterrupt:
                    print("\nStopping log extraction...")
                    process.terminate()
                    process.wait()
        else:
            print(f"Extracting logs to: {output_file}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(result.stdout)
            
            print(f"Successfully extracted {len(result.stdout.splitlines())} lines")
            
    except subprocess.CalledProcessError as e:
        print(f"Error extracting logs: {e}")
        return False
    except FileNotFoundError:
        print("Docker command not found. Make sure Docker is installed and running.")
        return False
    
    return True

def extract_timing_logs_only(container_name, output_file, lines=None):
    """Extract only timing-related logs from Docker container."""
    print(f"Extracting timing logs from container: {container_name}")
    
    cmd = ['docker', 'logs']
    if lines:
        cmd.extend(['--tail', str(lines)])
    cmd.append(container_name)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Filter for timing-related lines
        timing_lines = []
        for line in result.stdout.splitlines():
            if 'TIMING' in line or 'DICOM' in line:
                timing_lines.append(line)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(timing_lines))
        
        print(f"Successfully extracted {len(timing_lines)} timing-related lines")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"Error extracting logs: {e}")
        return False
    except FileNotFoundError:
        print("Docker command not found. Make sure Docker is installed and running.")
        return False

def main():
    parser = argparse.ArgumentParser(description='Extract Karnak timing logs from Docker container')
    parser.add_argument('container_name', default='karnak', nargs='?',
                       help='Docker container name (default: karnak)')
    parser.add_argument('--output', '-o', default='karnak_logs.txt',
                       help='Output file name (default: karnak_logs.txt)')
    parser.add_argument('--timing-only', '-t', action='store_true',
                       help='Extract only timing-related logs')
    parser.add_argument('--lines', '-n', type=int,
                       help='Number of lines to extract (default: all)')
    parser.add_argument('--follow', '-f', action='store_true',
                       help='Follow logs in real-time')
    parser.add_argument('--timestamp', action='store_true',
                       help='Add timestamp to output filename')
    
    args = parser.parse_args()
    
    # Add timestamp to filename if requested
    if args.timestamp:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name_parts = args.output.rsplit('.', 1)
        if len(name_parts) == 2:
            args.output = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
        else:
            args.output = f"{args.output}_{timestamp}"
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract logs
    if args.timing_only:
        success = extract_timing_logs_only(args.container_name, args.output, args.lines)
    else:
        success = extract_docker_logs(args.container_name, args.output, args.lines, args.follow)
    
    if success:
        print(f"Logs saved to: {output_path.absolute()}")
        
        # Show file size
        if output_path.exists():
            size = output_path.stat().st_size
            print(f"File size: {size:,} bytes")
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
