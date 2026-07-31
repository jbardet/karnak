#!/usr/bin/env python3
"""
CSV Timing Log Analyzer

This script finds and analyzes _timing_log.csv files in subfolders and
generates similar timing analysis graphs as the Karnak timing analyzer.
"""

import argparse
import json
import csv
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import glob


class CSVTimingAnalyzer:
    def __init__(self):
        self.timing_data = []
        self.summary_data = []

    def find_timing_csv_files(self, root_dir):
        """Find all _timing_log.csv files in subfolders of root directory."""
        root_path = Path(root_dir)
        if not root_path.exists():
            raise FileNotFoundError(f"Root directory not found: {root_dir}")

        # Use glob to find all _timing_log.csv files recursively
        pattern = str(root_path / "**" / "*_timing_log.csv")
        csv_files = glob.glob(pattern, recursive=True)

        print(f"Found {len(csv_files)} timing CSV files:")
        for file in csv_files:
            print(f"  {file}")

        return csv_files

    def parse_csv_file(self, csv_file):
        """Parse a single CSV timing log file."""
        print(f"Parsing: {csv_file}")

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, 1):
                    try:
                        # Extract data from CSV row
                        subject_id = row.get('subject_id', '')
                        timestamp = row.get('timestamp', '')
                        dicom_read = float(row.get('DICOM_READ_ms', 0))
                        tml_ctp_process = float(row.get('TML_CTP_PROCESS_ms', 0))
                        dicom_write = float(row.get('DICOM_WRITE_ms', 0))
                        total_processing = float(row.get('TOTAL_PROCESSING_ms', 0))

                        # Create summary data entry
                        summary_entry = {
                            'subject_id': subject_id,
                            'timestamp': timestamp,
                            'dicom_read_ms': dicom_read,
                            'tml_ctp_process_ms': tml_ctp_process,
                            'dicom_write_ms': dicom_write,
                            'total_ms': total_processing,
                            'source_file': csv_file
                        }

                        self.summary_data.append(summary_entry)

                    except (ValueError, KeyError) as e:
                        print(f"  Warning: Skipping row {row_num} in {csv_file}: {e}")
                        continue

        except (IOError, OSError) as e:
            print(f"  Error reading {csv_file}: {e}")
            return False

        parsed_count = len([d for d in self.summary_data
                           if d['source_file'] == csv_file])
        print(f"  Parsed {parsed_count} records")
        return True

    def parse_all_csv_files(self, root_dir):
        """Parse all CSV timing log files in the root directory."""
        csv_files = self.find_timing_csv_files(root_dir)

        if not csv_files:
            print("No _timing_log.csv files found!")
            return False

        for csv_file in csv_files:
            self.parse_csv_file(csv_file)

        print(f"\nTotal records parsed: {len(self.summary_data)}")
        return len(self.summary_data) > 0

    def save_to_csv(self, output_file):
        """Save timing data to CSV file."""
        if not self.summary_data:
            print("No data to save")
            return

        df = pd.DataFrame(self.summary_data)
        df.to_csv(output_file, index=False)
        print(f"Data saved to: {output_file}")

    def save_to_json(self, output_file):
        """Save timing data to JSON file."""
        data = {
            'summary_data': self.summary_data,
            'analysis_timestamp': datetime.now().isoformat(),
            'total_records': len(self.summary_data)
        }

        with open(output_file, 'w', encoding='utf-8') as f:
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
            'average_tml_ctp_process': df['tml_ctp_process_ms'].mean(),
            'average_dicom_write': df['dicom_write_ms'].mean(),
            'percentiles': {
                'p50': df['total_ms'].quantile(0.5),
                'p90': df['total_ms'].quantile(0.9),
                'p95': df['total_ms'].quantile(0.95),
                'p99': df['total_ms'].quantile(0.99)
            }
        }

        return stats

    def create_timing_graphs(self, output_dir='csv_timing_analysis'):
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
        plt.hist(df['total_ms'], bins=30, alpha=0.7, color='skyblue',
                 edgecolor='black')
        plt.title('Distribution of Total Processing Times')
        plt.xlabel('Processing Time (ms)')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{output_dir}/total_time_distribution.png', dpi=300,
                    bbox_inches='tight')
        plt.close()

        # 2. Phase Comparison Box Plot
        plt.figure(figsize=fig_size)
        phase_data = [df['dicom_read_ms'], df['tml_ctp_process_ms'],
                      df['dicom_write_ms']]
        phase_labels = ['DICOM_READ', 'TML_CTP_PROCESS', 'DICOM_WRITE']

        plt.boxplot(phase_data, labels=phase_labels)
        plt.title('Processing Time by Phase')
        plt.ylabel('Time (ms)')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.savefig(f'{output_dir}/phase_comparison_boxplot.png', dpi=300,
                    bbox_inches='tight')
        plt.close()

        # 3. Time Series Plot
        plt.figure(figsize=(15, 6))
        df_sorted = df.sort_values('timestamp')
        plt.plot(range(len(df_sorted)), df_sorted['total_ms'], 'b-',
                 alpha=0.7, linewidth=1)
        plt.title('Processing Time Over Time')
        plt.xlabel('File Sequence')
        plt.ylabel('Total Processing Time (ms)')
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{output_dir}/time_series.png', dpi=300,
                    bbox_inches='tight')
        plt.close()

        # 4. Phase Breakdown Pie Chart
        plt.figure(figsize=fig_size)
        avg_times = [df['dicom_read_ms'].mean(),
                     df['tml_ctp_process_ms'].mean(),
                     df['dicom_write_ms'].mean()]
        colors = ['#ff9999', '#66b3ff', '#99ff99']

        plt.pie(avg_times, labels=phase_labels, autopct='%1.1f%%',
                colors=colors, startangle=90)
        plt.title('Average Time Distribution by Phase')
        plt.savefig(f'{output_dir}/phase_pie_chart.png', dpi=300,
                    bbox_inches='tight')
        plt.close()

        # 5. Cumulative Distribution Function
        plt.figure(figsize=fig_size)
        sorted_times = np.sort(df['total_ms'])
        cumulative_prob = (np.arange(1, len(sorted_times) + 1) /
                           len(sorted_times))

        plt.plot(sorted_times, cumulative_prob, 'b-', linewidth=2)
        plt.title('Cumulative Distribution of Processing Times')
        plt.xlabel('Processing Time (ms)')
        plt.ylabel('Cumulative Probability')
        plt.grid(True, alpha=0.3)
        plt.savefig(f'{output_dir}/cumulative_distribution.png', dpi=300,
                    bbox_inches='tight')
        plt.close()

        # 6. Phase Correlation Heatmap
        plt.figure(figsize=(8, 6))
        correlation_data = df[['dicom_read_ms', 'tml_ctp_process_ms',
                               'dicom_write_ms', 'total_ms']]
        correlation_matrix = correlation_data.corr()

        plt.imshow(correlation_matrix, cmap='coolwarm', aspect='auto')
        plt.colorbar()
        plt.title('Phase Timing Correlation Matrix')

        # Add correlation values to the plot
        for i in range(len(correlation_matrix.columns)):
            for j in range(len(correlation_matrix.columns)):
                plt.text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                         ha='center', va='center', color='black')

        plt.xticks(range(len(correlation_matrix.columns)),
                   correlation_matrix.columns, rotation=45)
        plt.yticks(range(len(correlation_matrix.columns)),
                   correlation_matrix.columns)
        plt.savefig(f'{output_dir}/correlation_heatmap.png', dpi=300,
                    bbox_inches='tight')
        plt.close()

        print(f"Graphs saved to: {output_dir}/")

    def print_statistics_report(self):
        """Print a comprehensive statistics report."""
        stats = self.generate_statistics()

        if not stats:
            print("No timing data available for analysis")
            return

        print("\n" + "="*60)
        print("CSV TIMING LOG ANALYSIS")
        print("="*60)
        print(f"Total files processed: {stats['total_files_processed']}")
        timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Analysis timestamp: {timestamp_str}")
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
        print(f"DICOM_READ:      {stats['average_dicom_read']:.2f} ms")
        print(f"TML_CTP_PROCESS: {stats['average_tml_ctp_process']:.2f} ms")
        print(f"DICOM_WRITE:     {stats['average_dicom_write']:.2f} ms")

        # Calculate phase percentages and overhead
        total_avg = stats['average_total_time']
        phase_total = (stats['average_dicom_read'] +
                       stats['average_tml_ctp_process'] +
                       stats['average_dicom_write'])
        overhead = total_avg - phase_total
        overhead_percentage = (overhead / total_avg) * 100

        print("\nPHASE TIME PERCENTAGES:")
        print("-" * 40)
        read_pct = (stats['average_dicom_read']/total_avg)*100
        tml_pct = (stats['average_tml_ctp_process']/total_avg)*100
        write_pct = (stats['average_dicom_write']/total_avg)*100
        print(f"DICOM_READ:      {read_pct:.1f}%")
        print(f"TML_CTP_PROCESS: {tml_pct:.1f}%")
        print(f"DICOM_WRITE:     {write_pct:.1f}%")
        print(f"OVERHEAD:        {overhead_percentage:.1f}%")
        print("-" * 40)
        print(f"TOTAL:           {100:.1f}%")
        print("\nOVERHEAD BREAKDOWN:")
        print("-" * 40)
        print(f"Measured phases: {phase_total:.2f} ms")
        print(f"System overhead: {overhead:.2f} ms")
        print(f"Total time:      {total_avg:.2f} ms")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze CSV timing log files from subfolders')
    parser.add_argument('root_dir',
                        help='Root directory to search for _timing_log.csv files')
    parser.add_argument('--output-dir', default='csv_timing_analysis',
                        help='Output directory for analysis files '
                             '(default: csv_timing_analysis)')
    parser.add_argument('--csv', action='store_true',
                        help='Save data to CSV file')
    parser.add_argument('--json', action='store_true',
                        help='Save data to JSON file')
    parser.add_argument('--graphs', action='store_true',
                        help='Generate timing graphs')
    parser.add_argument('--stats', action='store_true',
                        help='Print statistics report')
    parser.add_argument('--all', action='store_true',
                        help='Run all analysis options')

    args = parser.parse_args()

    analyzer = CSVTimingAnalyzer()

    # Parse all CSV files
    if not analyzer.parse_all_csv_files(args.root_dir):
        print("No timing data found!")
        return

    # Create output directory
    Path(args.output_dir).mkdir(exist_ok=True)

    # Run analysis based on arguments
    if args.all or args.csv:
        analyzer.save_to_csv(f'{args.output_dir}/timing_data_summary.csv')

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
