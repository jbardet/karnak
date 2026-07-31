#!/usr/bin/env python3
"""
Karnak DICOM Processing Timing Analyzer

This script extracts timing information from Karnak logs and generates analysis reports.
"""

import re
import json
import csv
import argparse
from datetime import datetime
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

class KarnakTimingAnalyzer:
    def __init__(self):
        self.timing_data = []
        self.summary_data = []
        
    def parse_log_line(self, line):
        """Parse a single log line and extract timing information."""
        # Pattern for individual phase timing (handles both formatted and unformatted)
        phase_pattern = r'TIMING: \[([^\]]+)\] Completed phase (\w+) in ([\d.]+) ms'
        phase_match = re.search(phase_pattern, line)
        
        # Pattern for timing summary
        summary_pattern = r'TIMING_SUMMARY: \[([^\]]+)\] Total: ([\d.]+) ms \| DICOM_READ: ([\d.]+) ms \| KARNAK_PROCESS: ([\d.]+) ms \| DICOM_WRITE: ([\d.]+) ms'
        summary_match = re.search(summary_pattern, line)
        
        # Extract timestamp
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})'
        timestamp_match = re.search(timestamp_pattern, line)
        timestamp = timestamp_match.group(1) if timestamp_match else None
        
        if phase_match:
            sop_instance_uid = phase_match.group(1)
            phase = phase_match.group(2)
            timing_value = float(phase_match.group(3))
            
            return {
                'type': 'phase',
                'timestamp': timestamp,
                'sop_instance_uid': sop_instance_uid,
                'phase': phase,
                'timing_ms': timing_value
            }
        
        elif summary_match:
            sop_instance_uid = summary_match.group(1)
            total = float(summary_match.group(2))
            dicom_read = float(summary_match.group(3))
            karnak_process = float(summary_match.group(4))
            dicom_write = float(summary_match.group(5))
            
            return {
                'type': 'summary',
                'timestamp': timestamp,
                'sop_instance_uid': sop_instance_uid,
                'total_ms': total,
                'dicom_read_ms': dicom_read,
                'karnak_process_ms': karnak_process,
                'dicom_write_ms': dicom_write
            }
        
        return None
    
    def parse_logs(self, log_file):
        """Parse Karnak logs and extract timing data."""
        print(f"Parsing logs from: {log_file}")
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                parsed = self.parse_log_line(line)
                if parsed:
                    if parsed['type'] == 'phase':
                        self.timing_data.append(parsed)
                    else:
                        self.summary_data.append(parsed)
        
        print(f"Parsed {len(self.timing_data)} phase timings and {len(self.summary_data)} summaries")
    
    def save_to_csv(self, output_file):
        """Save timing data to CSV files."""
        # Save summary data
        summary_file = output_file.replace('.csv', '_summary.csv')
        if self.summary_data:
            df_summary = pd.DataFrame(self.summary_data)
            df_summary.to_csv(summary_file, index=False)
            print(f"Summary data saved to: {summary_file}")
        
        # Save phase data
        phase_file = output_file.replace('.csv', '_phases.csv')
        if self.timing_data:
            df_phases = pd.DataFrame(self.timing_data)
            df_phases.to_csv(phase_file, index=False)
            print(f"Phase data saved to: {phase_file}")
    
    def save_to_json(self, output_file):
        """Save timing data to JSON file."""
        data = {
            'summary_data': self.summary_data,
            'phase_data': self.timing_data,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_records': len(self.summary_data)
        }
        
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Data saved to: {output_file}")
    
    def generate_statistics(self):
        """Generate timing statistics."""
        if not self.summary_data:
            return {}
        
        df = pd.DataFrame(self.summary_data)
        
        stats = {
            'total_files_processed': len(df),
            'average_total_time': df['total_ms'].mean(),
            'median_total_time': df['total_ms'].median(),
            'min_total_time': df['total_ms'].min(),
            'max_total_time': df['total_ms'].max(),
            'std_total_time': df['total_ms'].std(),
            'average_dicom_read': df['dicom_read_ms'].mean(),
            'average_karnak_process': df['karnak_process_ms'].mean(),
            'average_dicom_write': df['dicom_write_ms'].mean(),
            'percentiles': {
                'p50': df['total_ms'].quantile(0.5),
                'p90': df['total_ms'].quantile(0.9),
                'p95': df['total_ms'].quantile(0.95),
                'p99': df['total_ms'].quantile(0.99)
            }
        }
        
        return stats
    
    def create_timing_graphs(self, output_dir='timing_analysis'):
        """Create various timing analysis graphs."""
        if not self.summary_data:
            print("No timing data available for graphing")
            return
        
        Path(output_dir).mkdir(exist_ok=True)
        df = pd.DataFrame(self.summary_data)
        
        # Set up the plotting style
        plt.style.use('default')
        fig_size = (12, 8)
        
        # 1. Total Processing Time Distribution
        plt.figure(figsize=fig_size)
        plt.hist(df['total_ms'], bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        plt.title('Distribution of Total Processing Times')
        plt.xlabel('Processing Time (ms)')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{output_dir}/total_time_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Phase Comparison Box Plot
        plt.figure(figsize=fig_size)
        phase_data = [df['dicom_read_ms'], df['karnak_process_ms'], df['dicom_write_ms']]
        phase_labels = ['DICOM_READ', 'KARNAK_PROCESS', 'DICOM_WRITE']
        
        plt.boxplot(phase_data, labels=phase_labels)
        plt.title('Processing Time by Phase')
        plt.ylabel('Time (ms)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.savefig(f'{output_dir}/phase_comparison_boxplot.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Time Series Plot
        plt.figure(figsize=(15, 6))
        df_sorted = df.sort_values('timestamp')
        plt.plot(range(len(df_sorted)), df_sorted['total_ms'], 'b-', alpha=0.7, linewidth=1)
        plt.title('Processing Time Over Time')
        plt.xlabel('File Sequence')
        plt.ylabel('Total Processing Time (ms)')
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{output_dir}/time_series.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 4. Phase Breakdown Pie Chart
        plt.figure(figsize=fig_size)
        avg_times = [df['dicom_read_ms'].mean(), df['karnak_process_ms'].mean(), df['dicom_write_ms'].mean()]
        colors = ['#ff9999', '#66b3ff', '#99ff99']
        
        plt.pie(avg_times, labels=phase_labels, autopct='%1.1f%%', colors=colors, startangle=90)
        plt.title('Average Time Distribution by Phase')
        plt.savefig(f'{output_dir}/phase_pie_chart.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 5. Cumulative Distribution Function
        plt.figure(figsize=fig_size)
        sorted_times = np.sort(df['total_ms'])
        cumulative_prob = np.arange(1, len(sorted_times) + 1) / len(sorted_times)
        
        plt.plot(sorted_times, cumulative_prob, 'b-', linewidth=2)
        plt.title('Cumulative Distribution of Processing Times')
        plt.xlabel('Processing Time (ms)')
        plt.ylabel('Cumulative Probability')
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{output_dir}/cumulative_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 6. Phase Correlation Heatmap
        plt.figure(figsize=(8, 6))
        correlation_data = df[['dicom_read_ms', 'karnak_process_ms', 'dicom_write_ms', 'total_ms']]
        correlation_matrix = correlation_data.corr()
        
        plt.imshow(correlation_matrix, cmap='coolwarm', aspect='auto')
        plt.colorbar()
        plt.title('Phase Timing Correlation Matrix')
        
        # Add correlation values to the plot
        for i in range(len(correlation_matrix.columns)):
            for j in range(len(correlation_matrix.columns)):
                plt.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}', 
                        ha='center', va='center', color='black')
        
        plt.xticks(range(len(correlation_matrix.columns)), correlation_matrix.columns, rotation=45)
        plt.yticks(range(len(correlation_matrix.columns)), correlation_matrix.columns)
        plt.savefig(f'{output_dir}/correlation_heatmap.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Graphs saved to: {output_dir}/")
    
    def print_statistics_report(self):
        """Print a comprehensive statistics report."""
        stats = self.generate_statistics()
        
        if not stats:
            print("No timing data available for analysis")
            return
        
        print("\n" + "="*60)
        print("KARNAK DICOM PROCESSING TIMING ANALYSIS")
        print("="*60)
        print(f"Total files processed: {stats['total_files_processed']}")
        print(f"Analysis timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nOVERALL PROCESSING TIME STATISTICS:")
        print("-" * 40)
        print(f"Average: {stats['average_total_time']:.2f} ms")
        print(f"Median:  {stats['median_total_time']:.2f} ms")
        print(f"Min:     {stats['min_total_time']:.2f} ms")
        print(f"Max:     {stats['max_total_time']:.2f} ms")
        print(f"Std Dev: {stats['std_total_time']:.2f} ms")
        
        print("\nPERCENTILES:")
        print("-" * 40)
        for p, value in stats['percentiles'].items():
            print(f"{p.upper()}: {value:.2f} ms")
        
        print("\nAVERAGE TIME BY PHASE:")
        print("-" * 40)
        print(f"DICOM_READ:    {stats['average_dicom_read']:.2f} ms")
        print(f"KARNAK_PROCESS: {stats['average_karnak_process']:.2f} ms")
        print(f"DICOM_WRITE:   {stats['average_dicom_write']:.2f} ms")
        
        # Calculate phase percentages and overhead
        total_avg = stats['average_total_time']
        phase_total = stats['average_dicom_read'] + stats['average_karnak_process'] + stats['average_dicom_write']
        overhead = total_avg - phase_total
        overhead_percentage = (overhead / total_avg) * 100
        
        print("\nPHASE TIME PERCENTAGES:")
        print("-" * 40)
        print(f"DICOM_READ:    {(stats['average_dicom_read']/total_avg)*100:.1f}%")
        print(f"KARNAK_PROCESS: {(stats['average_karnak_process']/total_avg)*100:.1f}%")
        print(f"DICOM_WRITE:   {(stats['average_dicom_write']/total_avg)*100:.1f}%")
        print(f"OVERHEAD:      {overhead_percentage:.1f}%")
        print("-" * 40)
        print(f"TOTAL:         {100:.1f}%")
        print("\nOVERHEAD BREAKDOWN:")
        print("-" * 40)
        print(f"Measured phases: {phase_total:.2f} ms")
        print(f"System overhead: {overhead:.2f} ms")
        print(f"Total time:      {total_avg:.2f} ms")
        print("="*60)

def main():
    parser = argparse.ArgumentParser(description='Analyze Karnak DICOM processing timing logs')
    parser.add_argument('log_file', help='Path to Karnak log file')
    parser.add_argument('--output-dir', default='timing_analysis', 
                       help='Output directory for analysis files (default: timing_analysis)')
    parser.add_argument('--csv', action='store_true', help='Save data to CSV files')
    parser.add_argument('--json', action='store_true', help='Save data to JSON file')
    parser.add_argument('--graphs', action='store_true', help='Generate timing graphs')
    parser.add_argument('--stats', action='store_true', help='Print statistics report')
    parser.add_argument('--all', action='store_true', help='Run all analysis options')
    
    args = parser.parse_args()
    
    analyzer = KarnakTimingAnalyzer()
    
    # Parse logs
    analyzer.parse_logs(args.log_file)
    
    if not analyzer.summary_data:
        print("No timing data found in the log file!")
        return
    
    # Create output directory
    Path(args.output_dir).mkdir(exist_ok=True)
    
    # Run analysis based on arguments
    if args.all or args.csv:
        analyzer.save_to_csv(f'{args.output_dir}/timing_data.csv')
    
    if args.all or args.json:
        analyzer.save_to_json(f'{args.output_dir}/timing_data.json')
    
    if args.all or args.graphs:
        analyzer.create_timing_graphs(args.output_dir)
    
    if args.all or args.stats:
        analyzer.print_statistics_report()
    
    if not any([args.csv, args.json, args.graphs, args.stats, args.all]):
        print("No analysis options specified. Use --help for available options.")
        print("Use --all to run all analysis options.")

if __name__ == '__main__':
    main()
