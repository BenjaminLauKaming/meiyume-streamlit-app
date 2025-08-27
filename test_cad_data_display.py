#!/usr/bin/env python3
"""
Test script to verify CAD data processing and display
"""

import json
import requests
import base64
import csv
import io

def test_cad_data_processing():
    """Test the CAD data processing functions"""
    
    # Load the latest result
    try:
        with open('backend/cad_results/latest_result.json', 'r') as f:
            latest_result = json.load(f)
        
        print("✅ Successfully loaded latest CAD result")
        print(f"Filename: {latest_result.get('filename', 'Unknown')}")
        print(f"Status: {latest_result.get('status', 'Unknown')}")
        
        # Check if we have CAD analysis data
        cad_analysis = latest_result.get('cad_analysis', {})
        if cad_analysis:
            print("✅ CAD analysis data found")
            print(f"Available keys: {list(cad_analysis.keys())}")
            
            # Test dimension data processing
            if 'dimension_decoded' in cad_analysis:
                print("✅ Dimension data found")
                dimension_csv = cad_analysis['dimension_decoded']
                
                # Test CSV parsing
                try:
                    # Remove BOM if present
                    if dimension_csv.startswith('\ufeff'):
                        dimension_csv = dimension_csv[1:]
                    
                    csv_reader = csv.DictReader(io.StringIO(dimension_csv))
                    rows = list(csv_reader)
                    
                    print(f"✅ Successfully parsed {len(rows)} dimension rows")
                    if rows:
                        print(f"Sample row: {dict(rows[0])}")
                        
                        # Test the conversion function
                        parts_dict = {}
                        for row in rows:
                            part_name = row.get('part_name', 'Unknown')
                            dimension_type = row.get('dimension_type', '')
                            feature = row.get('feature', '')
                            unit = row.get('unit', 'mm')
                            value = float(row.get('value', 0)) if row.get('value') else 0
                            tolerance = row.get('tolerance', '')
                            pages = [int(row.get('pages.0', 0))] if row.get('pages.0') else []
                            
                            # Create dimension object
                            dimension_obj = {
                                "dimension_type": dimension_type,
                                "feature": feature,
                                "unit": unit,
                                "value": value,
                                "tolerance": tolerance,
                                "pages": pages
                            }
                            
                            # Add to parts structure
                            if part_name not in parts_dict:
                                parts_dict[part_name] = {
                                    "part_name": part_name,
                                    "dimensions": [],
                                    "pages": []
                                }
                            
                            parts_dict[part_name]["dimensions"].append(dimension_obj)
                            parts_dict[part_name]["pages"].extend(pages)
                        
                        print(f"✅ Successfully converted to {len(parts_dict)} parts")
                        for part_name, part_data in parts_dict.items():
                            print(f"  - {part_name}: {len(part_data['dimensions'])} dimensions")
                        
                except Exception as e:
                    print(f"❌ Error parsing dimension CSV: {e}")
            
            # Test matching data processing
            if 'matching_decoded' in cad_analysis:
                print("✅ Matching data found")
                matching_csv = cad_analysis['matching_decoded']
                
                try:
                    # Remove BOM if present
                    if matching_csv.startswith('\ufeff'):
                        matching_csv = matching_csv[1:]
                    
                    csv_reader = csv.DictReader(io.StringIO(matching_csv))
                    rows = list(csv_reader)
                    
                    print(f"✅ Successfully parsed {len(rows)} matching rows")
                    if rows:
                        print(f"Sample matching row: {dict(rows[0])}")
                        
                except Exception as e:
                    print(f"❌ Error parsing matching CSV: {e}")
            
            # Test the API endpoint
            try:
                response = requests.get('http://localhost:8000/api/cad/latest/', timeout=10)
                if response.status_code == 200:
                    api_data = response.json()
                    print("✅ API endpoint working correctly")
                    print(f"API response status: {api_data.get('status')}")
                else:
                    print(f"❌ API endpoint returned status {response.status_code}")
            except Exception as e:
                print(f"❌ API endpoint error: {e}")
        
        else:
            print("❌ No CAD analysis data found")
            
    except FileNotFoundError:
        print("❌ Latest result file not found")
    except Exception as e:
        print(f"❌ Error loading latest result: {e}")

if __name__ == "__main__":
    test_cad_data_processing()
