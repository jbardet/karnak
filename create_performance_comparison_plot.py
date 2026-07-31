#!/usr/bin/env python3
"""
Create a performance comparison plot showing timing breakdown across datasets.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from pathlib import Path

def load_timing_data(file_path):
    """Load timing data from JSON file and calculate averages."""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    summary_data = data['summary_data']
    
    # Calculate averages for each timing component
    dicom_read_times = [item['dicom_read_ms'] for item in summary_data]
    karnak_process_times = [item['tml_ctp_process_ms'] for item in summary_data]
    # karnak_process_times = [item['karnak_process_ms'] for item in summary_data]
    dicom_write_times = [item['dicom_write_ms'] for item in summary_data]
    total_times = [item['total_ms'] for item in summary_data]
    
    # Calculate overhead time (total - read - process - write)
    overhead_times = [total - read - process - write 
                     for total, read, process, write in zip(total_times, dicom_read_times, karnak_process_times, dicom_write_times)]
    
    return {
        'dicom_read_avg': np.mean(dicom_read_times),
        'dicom_write_avg': np.mean(dicom_write_times),
        'karnak_process_avg': np.mean(karnak_process_times),
        'overhead_avg': np.mean(overhead_times),
        'total_avg': np.mean(total_times),
        'dicom_read_std': np.std(dicom_read_times),
        'dicom_write_std': np.std(dicom_write_times),
        'karnak_process_std': np.std(karnak_process_times),
        'overhead_std': np.std(overhead_times),
        'total_std': np.std(total_times)
    }

def create_performance_plot():
    """Create the performance comparison plot."""
    
    # Dataset paths and display names.
    # Labels are deliberately generic: they become the x-axis tick labels, so
    # they must not carry contributor or patient identifiers.
    # datasets = {
    #     'fMRI 7T': 'timing_analysis_7T_fMRI_validation_subject10_complete/timing_data.json',
    #     'RSNA': 'timing_analysis_RSNA_sample/timing_data.json',
    #     'Target': 'timing_analysis_Target/timing_data.json',
    #     'HEART': 'timing_analysis_4d/timing_data.json'
    # }
    datasets = {
        'fMRI 7T': 'csv_timing_analysis_7t/timing_data.json',
        'RSNA': 'csv_timing_analysis_rsna/timing_data.json',
        'Target': 'csv_timing_analysis_Target/timing_data.json',
        'HEART': 'csv_timing_analysis_Heart/timing_data.json'
    }
    
    # Load data for all datasets
    dataset_data = {}
    for name, path in datasets.items():
        if Path(path).exists():
            dataset_data[name] = load_timing_data(path)
        else:
            print(f"Warning: {path} not found")
    
    # Prepare data for plotting
    dataset_names = list(dataset_data.keys())
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Set up the bar positions - two bars per dataset
    x = np.arange(len(dataset_names))
    width = 0.35  # Width of each bar
    
    # Calculate percentages for each component
    dicom_read_percentages = []
    dicom_write_percentages = []
    karnak_process_percentages = []
    overhead_percentages = []
    
    for name in dataset_names:
        data = dataset_data[name]
        total_ms = data['total_avg']
        
        # Calculate percentages
        dicom_read_percentages.append(data['dicom_read_avg'] / total_ms * 100)
        dicom_write_percentages.append(data['dicom_write_avg'] / total_ms * 100)
        karnak_process_percentages.append(data['karnak_process_avg'] / total_ms * 100)
        overhead_percentages.append(data['overhead_avg'] / total_ms * 100)
    
    # Create the grouped bars
    # First bar group: DICOM I/O (read + write)
    ax.bar(x - width/2, dicom_read_percentages, width, label='DICOM Read', color='#FF6B6B', alpha=0.8)
    ax.bar(x - width/2, dicom_write_percentages, width, bottom=dicom_read_percentages, label='DICOM Write', color='#4ECDC4', alpha=0.8)
    
    # Second bar group: Karnak Processing (process + overhead)
    ax.bar(x + width/2, karnak_process_percentages, width, label='Karnak Processing', color='#45B7D1', alpha=0.8)
    ax.bar(x + width/2, overhead_percentages, width, bottom=karnak_process_percentages, label='Overhead', color='#96CEB4', alpha=0.8)
    
    # Customize the plot
    ax.set_xlabel('Dataset', fontsize=12, fontweight='bold')
    ax.set_ylabel('Percentage of Total Time (%)', fontsize=12, fontweight='bold')
    ax.set_title('Performance Breakdown Across Datasets\nDICOM I/O vs CPU Karnak Processing', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(dataset_names, rotation=45, ha='right')
    ax.set_ylim(0, 100)
    
    # Add grid
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_axisbelow(True)
    
    # Add legend
    ax.legend(loc='upper right', bbox_to_anchor=(1, 1))
    
    # Add percentage labels on bars
    for i, name in enumerate(dataset_names):
        # DICOM I/O bar labels
        dicom_read = dicom_read_percentages[i]
        dicom_write = dicom_write_percentages[i]
        dicom_total = dicom_read + dicom_write
        
        # Label for DICOM read portion
        if dicom_read > 1:  # Only show if significant (>1%)
            ax.text(i - width/2, dicom_read/2, f'{dicom_read:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9, color='white')
        
        # Label for DICOM write portion
        if dicom_write > 1:  # Only show if significant (>1%)
            ax.text(i - width/2, dicom_read + dicom_write/2, f'{dicom_write:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9, color='white')
        
        # Total percentage label on top of DICOM I/O bar
        ax.text(i - width/2, dicom_total + 2, f'{dicom_total:.1f}%', 
                ha='center', va='bottom', fontweight='bold', fontsize=10, color='black')
        
        # Karnak Processing bar labels
        karnak_process = karnak_process_percentages[i]
        overhead = overhead_percentages[i]
        karnak_total = karnak_process + overhead
        
        # Label for Karnak processing portion
        if karnak_process > 1:  # Only show if significant (>1%)
            ax.text(i + width/2, karnak_process/2, f'{karnak_process:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9, color='white')
        
        # Label for overhead portion
        if overhead > 1:  # Only show if significant (>1%)
            ax.text(i + width/2, karnak_process + overhead/2, f'{overhead:.1f}%', 
                    ha='center', va='center', fontweight='bold', fontsize=9, color='white')
        
        # Total percentage label on top of Karnak Processing bar
        ax.text(i + width/2, karnak_total + 2, f'{karnak_total:.1f}%', 
                ha='center', va='bottom', fontweight='bold', fontsize=10, color='black')
    
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    output_file = 'performance_breakdown_comparison.png'
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Plot saved as: {output_file}")
    
    # Show the plot
    plt.show()

if __name__ == "__main__":
    create_performance_plot()
