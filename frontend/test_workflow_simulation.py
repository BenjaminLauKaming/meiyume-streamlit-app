"""
Test Workflow Simulation Script
Simulates the entire CAD analysis workflow without calling real services
"""

import streamlit as st
import time
import json
import uuid
from datetime import datetime, timezone
import pandas as pd
from io import BytesIO

def generate_fake_cad_results():
    """Generate realistic fake CAD analysis results"""
    return {
        "results": [
            {
                "result_type": "dimensions",
                "raw_data": {
                    "parts": [
                        {
                            "name": "Perfume Cap",
                            "dimensions": [
                                {"name": "Outer Diameter", "value": 24.5, "unit": "mm", "tolerance": "±0.1", "critical": True},
                                {"name": "Inner Diameter", "value": 22.3, "unit": "mm", "tolerance": "±0.1", "critical": True},
                                {"name": "Height", "value": 15.2, "unit": "mm", "tolerance": "±0.2", "critical": False},
                                {"name": "Thread Pitch", "value": 1.5, "unit": "mm", "tolerance": "±0.05", "critical": True},
                                {"name": "Wall Thickness", "value": 1.1, "unit": "mm", "tolerance": "±0.1", "critical": False}
                            ]
                        },
                        {
                            "name": "Spray Head",
                            "dimensions": [
                                {"name": "Nozzle Diameter", "value": 0.8, "unit": "mm", "tolerance": "±0.02", "critical": True},
                                {"name": "Body Diameter", "value": 12.5, "unit": "mm", "tolerance": "±0.1", "critical": False},
                                {"name": "Length", "value": 28.7, "unit": "mm", "tolerance": "±0.2", "critical": False},
                                {"name": "Spring Travel", "value": 3.2, "unit": "mm", "tolerance": "±0.1", "critical": True},
                                {"name": "Actuator Force", "value": 2.5, "unit": "N", "tolerance": "±0.3", "critical": True}
                            ]
                        },
                        {
                            "name": "Bottle Neck",
                            "dimensions": [
                                {"name": "External Thread Diameter", "value": 22.0, "unit": "mm", "tolerance": "±0.1", "critical": True},
                                {"name": "Internal Diameter", "value": 18.5, "unit": "mm", "tolerance": "±0.1", "critical": False},
                                {"name": "Thread Height", "value": 8.0, "unit": "mm", "tolerance": "±0.1", "critical": False},
                                {"name": "Neck Height", "value": 25.0, "unit": "mm", "tolerance": "±0.2", "critical": False},
                                {"name": "Shoulder Radius", "value": 5.0, "unit": "mm", "tolerance": "±0.2", "critical": False}
                            ]
                        }
                    ],
                    "contact_pairs": [
                        {
                            "part1": "Perfume Cap",
                            "part2": "Bottle Neck", 
                            "contact_type": "Thread Connection",
                            "fit_status": "Good Fit",
                            "clearance": 0.2,
                            "unit": "mm"
                        },
                        {
                            "part1": "Spray Head",
                            "part2": "Bottle Neck",
                            "contact_type": "Press Fit",
                            "fit_status": "Tight Fit", 
                            "clearance": -0.1,
                            "unit": "mm"
                        },
                        {
                            "part1": "Perfume Cap",
                            "part2": "Spray Head",
                            "contact_type": "Clearance Fit",
                            "fit_status": "Good Fit",
                            "clearance": 0.3,
                            "unit": "mm"
                        },
                        {
                            "part1": "Bottle Neck",
                            "part2": "Perfume Cap",
                            "contact_type": "Sealing Surface",
                            "fit_status": "Perfect Fit",
                            "clearance": 0.05,
                            "unit": "mm"
                        }
                    ]
                }
            }
        ]
    }

def simulate_workflow_processing():
    """Simplified workflow simulation with just progress bar and status"""
    steps = [
        ("📤 Uploading file to Django backend...", 0.15),
        ("⚙️ Django processing file and preparing for n8n...", 0.30),
        ("🔄 Starting n8n workflow...", 0.45),
        ("📡 Uploading file to Gemini AI...", 0.60),
        ("🤖 Gemini AI analyzing CAD drawing...", 0.85),
        ("📤 Sending results back to Django...", 1.0)
    ]
    
    # Create containers
    progress_bar = st.progress(0)
    status_container = st.empty()
    
    # Simulate processing
    for step_text, progress in steps:
        status_container.info(step_text)
        progress_bar.progress(progress)
        time.sleep(0.8)  # Shorter delay
    
    # Final success message
    status_container.success("✅ Analysis completed successfully!")
    time.sleep(0.5)
    
    return generate_fake_cad_results()

def display_results_spreadsheet(results_data):
    """Display CAD analysis results in a beautiful spreadsheet format"""
    st.subheader("📈 Analysis Results - Spreadsheet View")
    
    # Create tabs for different result types
    tabs = st.tabs(["📊 Parts & Dimensions", "🔗 Part Relationships", "📋 Summary", "📥 Downloads"])
    
    with tabs[0]:
        st.markdown("### 📏 Parts and Dimensions Analysis")
        
        # Find the dimensions result
        dimensions_result = None
        for result in results_data.get("results", []):
            if result.get("result_type") == "dimensions":
                dimensions_result = result
                break
        
        if dimensions_result and "parts" in dimensions_result.get("raw_data", {}):
            parts_data = dimensions_result["raw_data"]["parts"]
            
            # Create a comprehensive dataframe for all parts and dimensions
            all_dimensions = []
            
            for part in parts_data:
                part_name = part.get("name", "Unknown Part")
                dimensions = part.get("dimensions", [])
                
                for dim in dimensions:
                    all_dimensions.append({
                        "Part Name": part_name,
                        "Feature": dim.get("name", ""),
                        "Value": dim.get("value", ""),
                        "Tolerance": dim.get("tolerance", ""),
                        "Unit": dim.get("unit", ""),
                        "Critical": "✅" if dim.get("critical", False) else "❌"
                    })
            
            if all_dimensions:
                df = pd.DataFrame(all_dimensions)
                
                # Display the dataframe with styling
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Part Name": st.column_config.TextColumn("Part Name", width="medium"),
                        "Feature": st.column_config.TextColumn("Feature", width="large"),
                        "Value": st.column_config.NumberColumn("Value", format="%.3f"),
                        "Tolerance": st.column_config.TextColumn("Tolerance", width="small"),
                        "Unit": st.column_config.TextColumn("Unit", width="small"),
                        "Critical": st.column_config.TextColumn("Critical", width="small")
                    }
                )
                
                # Add filters and search
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    part_filter = st.selectbox(
                        "Filter by Part",
                        ["All Parts"] + list(df["Part Name"].unique())
                    )
                
                with col2:
                    critical_only = st.checkbox("Show Critical Dimensions Only")
                
                # Apply filters
                filtered_df = df.copy()
                if part_filter != "All Parts":
                    filtered_df = filtered_df[filtered_df["Part Name"] == part_filter]
                if critical_only:
                    filtered_df = filtered_df[filtered_df["Critical"] == "✅"]
                
                if len(filtered_df) != len(df):
                    st.markdown(f"**Showing {len(filtered_df)} of {len(df)} dimensions**")
                    st.dataframe(filtered_df, use_container_width=True, hide_index=True)
                
                # Summary statistics
                st.markdown("---")
                st.markdown("### 📊 Summary Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Parts", len(parts_data))
                
                with col2:
                    st.metric("Total Dimensions", len(all_dimensions))
                
                with col3:
                    critical_count = len([d for d in all_dimensions if d["Critical"] == "✅"])
                    st.metric("Critical Dimensions", critical_count)
                
                with col4:
                    interior_count = len([d for d in all_dimensions if d["Critical"] == "❌"])
                    st.metric("Interior Dimensions", interior_count)
                
            else:
                st.info("No dimension data available")
        else:
            st.info("No dimension data available")
    
    with tabs[1]:
        st.markdown("### 🔗 Part Relationships & Fits")
        
        if dimensions_result and "contact_pairs" in dimensions_result.get("raw_data", {}):
            contact_pairs = dimensions_result["raw_data"]["contact_pairs"]
            
            if contact_pairs:
                # Create relationship dataframe
                relationships = []
                
                for pair in contact_pairs:
                    relationships.append({
                        "Part A": pair.get("part1", ""),
                        "Part B": pair.get("part2", ""),
                        "Contact Type": pair.get("contact_type", ""),
                        "Fit Status": pair.get("fit_status", ""),
                        "Clearance": f"{pair.get('clearance', '0')} {pair.get('unit', '')}"
                    })
                
                rel_df = pd.DataFrame(relationships)
                
                # Display with styling
                st.dataframe(
                    rel_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Part A": st.column_config.TextColumn("Part A", width="medium"),
                        "Part B": st.column_config.TextColumn("Part B", width="medium"),
                        "Contact Type": st.column_config.TextColumn("Contact Type", width="large"),
                        "Fit Status": st.column_config.TextColumn("Fit Status", width="large"),
                        "Clearance": st.column_config.TextColumn("Clearance", width="small")
                    }
                )
                
                # Fit status summary
                st.markdown("---")
                st.markdown("### 🎯 Fit Analysis Summary")
                
                fit_counts = rel_df["Fit Status"].value_counts()
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    compatible = fit_counts.get("Good Fit", 0)
                    st.metric("✅ Compatible", compatible)
                
                with col2:
                    tight = fit_counts.get("Tight Fit", 0)
                    st.metric("⚠️ Tight Fit", tight)
                
                with col3:
                    loose = fit_counts.get("Good Fit", 0)
                    st.metric("❌ Too Loose", loose)
                
                with col4:
                    interference = fit_counts.get("Perfect Fit", 0)
                    st.metric("🎯 Perfect Fit", interference)
                
            else:
                st.info("No part relationships detected")
        else:
            st.info("No relationship data available")
    
    with tabs[2]:
        st.markdown("### 📋 Analysis Summary")
        
        if dimensions_result:
            # Extract summary data
            parts_data = dimensions_result["raw_data"].get("parts", [])
            contact_pairs = dimensions_result["raw_data"].get("contact_pairs", [])
            
            # Create summary metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📏 Dimension Summary")
                
                total_dimensions = sum(len(part.get("dimensions", [])) for part in parts_data)
                critical_dimensions = sum(
                    sum(1 for dim in part.get("dimensions", []) if dim.get("critical", False))
                    for part in parts_data
                )
                
                st.metric("Total Parts Analyzed", len(parts_data))
                st.metric("Total Dimensions", total_dimensions)
                st.metric("Critical Dimensions", critical_dimensions)
                st.metric("Part Relationships", len(contact_pairs))
            
            with col2:
                st.markdown("#### 🎯 Quality Metrics")
                
                if total_dimensions > 0:
                    critical_percentage = (critical_dimensions / total_dimensions) * 100
                    st.metric("Critical Dimension %", f"{critical_percentage:.1f}%")
                
                if contact_pairs:
                    compatible_pairs = sum(1 for pair in contact_pairs if pair.get("fit_status") == "Good Fit")
                    compatibility_rate = (compatible_pairs / len(contact_pairs)) * 100
                    st.metric("Compatibility Rate", f"{compatibility_rate:.1f}%")
            
            # Part breakdown
            st.markdown("---")
            st.markdown("#### 📊 Part Breakdown")
            
            if parts_data:
                part_summary = []
                for part in parts_data:
                    part_name = part.get("name", "Unknown")
                    dimensions = part.get("dimensions", [])
                    critical_count = sum(1 for dim in dimensions if dim.get("critical", False))
                    
                    part_summary.append({
                        "Part Name": part_name,
                        "Total Dimensions": len(dimensions),
                        "Critical Dimensions": critical_count,
                        "Features": ", ".join([dim.get("name", "") for dim in dimensions])
                    })
                
                summary_df = pd.DataFrame(part_summary)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
    
    with tabs[3]:
        st.subheader("📥 Download Results")
        
        if dimensions_result:
            # Generate downloadable files
            
            # Create dimensions CSV
            if "parts" in dimensions_result["raw_data"]:
                all_dimensions = []
                for part in dimensions_result["raw_data"]["parts"]:
                    part_name = part.get("name", "Unknown Part")
                    for dim in part.get("dimensions", []):
                        all_dimensions.append({
                            "Part Name": part_name,
                            "Feature": dim.get("name", ""),
                            "Value": dim.get("value", ""),
                            "Tolerance": dim.get("tolerance", ""),
                            "Unit": dim.get("unit", ""),
                            "Critical": dim.get("critical", False)
                        })
                
                if all_dimensions:
                    df_dimensions = pd.DataFrame(all_dimensions)
                    csv_buffer = BytesIO()
                    df_dimensions.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    
                    st.download_button(
                        label="📊 Download Dimensions (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name="cad_dimensions.csv",
                        mime="text/csv"
                    )
            
            # Create relationships CSV
            if "contact_pairs" in dimensions_result["raw_data"]:
                relationships = dimensions_result["raw_data"]["contact_pairs"]
                if relationships:
                    df_relationships = pd.DataFrame(relationships)
                    csv_buffer = BytesIO()
                    df_relationships.to_csv(csv_buffer, index=False)
                    csv_buffer.seek(0)
                    
                    st.download_button(
                        label="🔗 Download Relationships (CSV)",
                        data=csv_buffer.getvalue(),
                        file_name="cad_relationships.csv",
                        mime="text/csv"
                    )
            
            # Download full JSON report
            json_buffer = BytesIO()
            json_str = json.dumps(dimensions_result["raw_data"], indent=2)
            json_buffer.write(json_str.encode('utf-8'))
            json_buffer.seek(0)
            
            st.download_button(
                label="📄 Download Full Report (JSON)",
                data=json_buffer.getvalue(),
                file_name="cad_analysis_report.json",
                mime="application/json"
            )
        
        st.info("💡 Tip: Use the CSV files to import data into Excel or other spreadsheet applications for further analysis.")

def run_workflow_simulation():
    """Main function to run the complete workflow simulation"""
    
    st.title("🧪 CAD Workflow Simulation")
    st.markdown("### Testing the complete workflow with realistic data")
    
    # Show simulation info
    st.info("""
    **This simulation will:**
    1. 📤 Simulate file upload to Django
    2. ⚙️ Show Django processing steps
    3. 🔄 Simulate n8n workflow execution
    4. 📡 Show Gemini AI analysis progress
    5. 📤 Simulate results callback
    6. 💾 Show final data processing
    7. 📊 Display beautiful spreadsheet results
    """)
    
    # Start simulation button
    if st.button("🚀 Start Workflow Simulation", type="primary", use_container_width=True):
        
        # Create a container for the simulation
        simulation_container = st.container()
        
        with simulation_container:
            st.markdown("---")
            st.markdown("### 🔄 Workflow Simulation in Progress...")
            
            # Run the simulation
            results = simulate_workflow_processing()
            
            st.markdown("---")
            st.markdown("### 📊 Displaying Results...")
            
            # Display results
            display_results_spreadsheet(results)
            
            # Show simulation completion
            st.success("🎉 **Simulation completed successfully!**")
            st.info("💡 This is exactly how real uploads will work, but with your actual data!")

if __name__ == "__main__":
    run_workflow_simulation() 