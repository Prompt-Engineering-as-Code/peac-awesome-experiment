#!/usr/bin/env python3
"""
Test script for metrics calculation functions.
"""

import os
from common import (
    calculate_token_reduction_ratio, 
    calculate_reuse_efficiency, 
    calculate_modularity_index
)

def main():
    # Directory paths
    original_dir = "peac_modules_single"
    refactored_dir = "refactored_peac_modules"
    
    # Check if directories exist
    if not os.path.exists(original_dir):
        print(f"Error: Directory {original_dir} not found")
        return
    
    if not os.path.exists(refactored_dir):
        print(f"Error: Directory {refactored_dir} not found")
        return
    
    print("Calculating PEaC Modularization Metrics...")
    print("=" * 50)
    
    # Calculate Token Reduction Ratio (TRR)
    print("1. Calculating Token Reduction Ratio (TRR)...")
    trr = calculate_token_reduction_ratio(original_dir, refactored_dir)
    print(f"   TRR = {trr:.2f}%")
    
    # Calculate Reuse Efficiency (RE)
    print("2. Calculating Reuse Efficiency (RE)...")
    re = calculate_reuse_efficiency(original_dir, refactored_dir)
    print(f"   RE = {re:.2f}%")
    
    # Calculate Modularity Index (MI)
    print("3. Calculating Modularity Index (MI)...")
    mi = calculate_modularity_index(refactored_dir)
    print(f"   MI = {mi:.2f}")
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    print(f"Token Reduction Ratio (TRR):   {trr:.2f}%")
    print(f"Reuse Efficiency (RE):         {re:.2f}%") 
    print(f"Modularity Index (MI):         {mi:.2f}")
    
    # Analysis
    print("\nANALYSIS:")
    if trr > 0:
        print(f"✓ Modularization achieved {trr:.1f}% token reduction")
    else:
        print(f"✗ No token reduction achieved (TRR = {trr:.1f}%)")
    
    if re > 50:
        print(f"✓ High reuse efficiency ({re:.1f}%) - base modules are well utilized")
    elif re > 20:
        print(f"~ Moderate reuse efficiency ({re:.1f}%)")
    else:
        print(f"✗ Low reuse efficiency ({re:.1f}%) - limited base module utilization")
    
    if mi > 0.5:
        print(f"✓ Good modular structure (MI = {mi:.2f}) - rich composition")
    elif mi > 0.2:
        print(f"~ Moderate modular structure (MI = {mi:.2f})")
    else:
        print(f"✗ Limited modular structure (MI = {mi:.2f}) - few base modules used")

if __name__ == "__main__":
    main()