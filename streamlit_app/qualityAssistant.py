import streamlit as st
import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

# Configuration
DJANGO_API_URL = os.getenv("DJANGO_API_URL", "http://localhost:8000")

def generate_test_list(product_type, protocol, specifications):
    """Generate test list based on product type and protocol"""
    # This would integrate with your AI service (Gemini) to generate test lists
    # For now, we'll create sample test lists based on common scenarios
    
    sample_tests = {
        "lipstick": {
            "dior": [
                "Color consistency test across batches",
                "Texture smoothness evaluation",
                "Application uniformity assessment",
                "Wear resistance test (8-hour duration)",
                "Smudge resistance evaluation",
                "Color payoff intensity measurement",
                "Packaging integrity check",
                "Temperature stability test (-5°C to 45°C)",
                "Microbiology safety testing",
                "Heavy metals content analysis",
                "Fragrance stability assessment",
                "pH level verification (6.5-7.5)",
                "Moisture content analysis",
                "Shelf life stability test (24 months)",
                "Consumer sensory evaluation"
            ],
            "generic": [
                "Basic color consistency check",
                "Application test",
                "Wear test (4 hours)",
                "Safety testing",
                "Packaging check"
            ]
        },
        "foundation": {
            "dior": [
                "Shade matching accuracy test",
                "Coverage consistency evaluation",
                "Oxidation resistance test",
                "Skin tone compatibility assessment",
                "Blendability performance test",
                "Longevity test (12-hour wear)",
                "Transfer resistance evaluation",
                "SPF verification (if applicable)",
                "Skin sensitivity testing",
                "Photostability assessment",
                "Humidity resistance test",
                "Temperature stability evaluation"
            ]
        },
        "skincare": {
            "dior": [
                "Ingredient purity verification",
                "pH balance testing",
                "Viscosity consistency check",
                "Absorption rate evaluation",
                "Skin compatibility testing",
                "Efficacy testing (clinical trials)",
                "Packaging sterility verification",
                "Preservative effectiveness test",
                "Stability under various conditions",
                "Texture consistency evaluation"
            ]
        }
    }
    
    # Get tests based on product and protocol
    if product_type.lower() in sample_tests:
        if protocol.lower() in sample_tests[product_type.lower()]:
            return sample_tests[product_type.lower()][protocol.lower()]
        else:
            return sample_tests[product_type.lower()].get("generic", [])
    
    # Generic fallback
    return [
        "Basic functionality test",
        "Safety compliance check",
        "Quality standards verification",
        "Performance evaluation",
        "User acceptance testing"
    ]

def quality_assistant():
    """Quality Assistant main interface"""
    st.title("🎯 Quality Assistant")
    st.markdown("### Automated Test List Generation for Quality Control")
    
    # Quick info banner
    st.info("💡 Generate comprehensive test lists tailored to your product and quality protocol requirements")
    
    # Main form
    with st.form("test_generation_form"):
        st.subheader("📋 Project Specifications")
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_type = st.selectbox(
                "Product Type",
                [
                    "Perfume Cap",
                    "Lipstick",
                    "Compact", 
                    "jar",
                    "Glass",
                    "Stock item",
                    "Accesssory",
                    "Other"
                ],
                help="Select the type of product you need to test"
            )
            
            if product_type == "Other":
                custom_product = st.text_input("Specify Product Type")
                product_type = custom_product if custom_product else "Generic Product"
        
        
        with col2:
            protocol = st.selectbox(
                "Quality Protocol/Standard",
                [
                    "MYM Internal Standard",
                    "Dior Standard",
                    "LVMH Standard"
                    "PUIG Standard",
                ],
                help="Select the quality protocol or standard to follow"
            )
            
            if protocol == "Custom Protocol":
                custom_protocol = st.text_input("Specify Protocol Name")
                protocol = custom_protocol if custom_protocol else "Custom"
        
        st.markdown("---")
        
        # Additional specifications
        st.subheader("🔧 Additional Specifications")
        
        col3, col4 = st.columns(2)
        
        with col3:

            test_severity = st.selectbox(
                "Test Severity",
                ["Mass Item", "Masstige Item", "prestige Item"]
            )

        
        with col4:

            test_bulk = st.radio(
                "Test Bulk",
                ["Bulk (liquid)", "Bulk (solid)", "Other"]
            )
    
        
        # Special requirements
        special_requirements = st.text_area(
            "Special Requirements or Notes",
            placeholder="e.g., Vegan formulation, Sensitive skin compatibility, Specific color requirements...",
            help="Add any special requirements or considerations for testing"
        )
        
        # Submit button
        submitted = st.form_submit_button("🚀 Generate Test List", type="primary", use_container_width=True)
    
    # Process form submission
    if submitted:
        with st.spinner("Generating customized test list..."):
            # Simulate processing time
            time.sleep(2)
            
            specifications = {

                "test_severity": test_severity,
                "test_bulk": test_bulk,
    \
            
                "special_requirements": special_requirements
            }
            
            test_list = generate_test_list(product_type, protocol, specifications)
            
            # Display results
            st.success(f"✅ Test list generated successfully for {product_type} using {protocol}!")
            
            # Test list display
            st.subheader("📋 Generated Test List")
            
            # Summary card
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Total Tests", len(test_list))
            with col2:
                estimated_time = len(test_list) * 2  # 2 hours per test average
                st.metric("⏱️ Est. Time", f"{estimated_time}h")
            with col3:
                st.metric("🎯 Protocol", protocol.split()[0])
            with col4:
                st.metric("📦 Product", product_type)
            
            st.markdown("---")
            
            # Test list with checkboxes
            st.subheader("✅ Test Checklist")
            
            # Create tabs for different categories
            tabs = st.tabs(["🔬 All Tests", "📊 Summary", "📥 Export"])
            
            with tabs[0]:
                for i, test in enumerate(test_list, 1):
                    with st.expander(f"Test {i}: {test}"):
                        col_a, col_b, col_c = st.columns([2, 1, 1])
                        
                        with col_a:
                            completed = st.checkbox(f"Mark as completed", key=f"test_{i}")
                            
                        with col_b:
                            priority = st.selectbox(
                                "Priority",
                                ["High", "Medium", "Low"],
                                key=f"priority_{i}",
                                index=0 if i <= 5 else 1
                            )
                        
                        with col_c:
                            assigned_to = st.text_input(
                                "Assigned to",
                                placeholder="Tester name",
                                key=f"assigned_{i}"
                            )
                        
                        # Notes section
                        notes = st.text_area(
                            "Test Notes",
                            placeholder="Add specific instructions or observations...",
                            key=f"notes_{i}"
                        )
            
            with tabs[1]:
                st.markdown("### 📊 Test Summary Report")
                
                # Project info
                st.markdown(f"**Product:** {product_type}")
                st.markdown(f"**Protocol:** {protocol}")
         
        
                
                if special_requirements:
                    st.markdown(f"**Special Requirements:** {special_requirements}")
                
                st.markdown("---")
                
                st.markdown("### 📋 Test Categories Breakdown")
                # Categorize tests (simplified)
                safety_tests = [test for test in test_list if any(word in test.lower() for word in ['safety', 'toxicity', 'sensitivity', 'microbiology'])]
                performance_tests = [test for test in test_list if any(word in test.lower() for word in ['performance', 'wear', 'durability', 'resistance'])]
                quality_tests = [test for test in test_list if any(word in test.lower() for word in ['consistency', 'color', 'texture', 'quality'])]
                compliance_tests = [test for test in test_list if any(word in test.lower() for word in ['compliance', 'regulation', 'standard', 'verification'])]
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🛡️ Safety Tests", len(safety_tests))
                with col2:
                    st.metric("⚡ Performance Tests", len(performance_tests))
                with col3:
                    st.metric("✨ Quality Tests", len(quality_tests))
                with col4:
                    st.metric("📜 Compliance Tests", len(compliance_tests))
            
            with tabs[2]:
                st.markdown("### 📥 Export Options")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📄 Export as PDF", use_container_width=True):
                        st.info("PDF export functionality coming soon!")
                    
                    if st.button("📊 Export as Excel", use_container_width=True):
                        st.info("Excel export functionality coming soon!")
                
                with col2:
                    if st.button("📧 Email Test List", use_container_width=True):
                        st.info("Email functionality coming soon!")
                    
                    if st.button("🔗 Share Link", use_container_width=True):
                        st.info("Share link functionality coming soon!")
                
                # Raw text export
                st.markdown("### 📝 Raw Test List")
                test_list_text = "\n".join([f"{i+1}. {test}" for i, test in enumerate(test_list)])
                st.text_area(
                    "Copy test list:",
                    value=test_list_text,
                    height=200,
                    help="Copy this text to use in other applications"
                )
    
    # Sidebar with recent projects and templates
    with st.sidebar:
        st.subheader("📚 Recent Projects")
        
        # Mock recent projects
        recent_projects = [
            {"product": "Lipstick Rouge", "protocol": "Dior", "date": "2024-01-15"},
     
        ]
        
        for project in recent_projects:
            with st.expander(f"🔬 {project['product']}"):
                st.write(f"Protocol: {project['protocol']}")
                st.write(f"Date: {project['date']}")
                if st.button(f"Reload", key=f"reload_{project['product']}"):
                    st.info("Project reload coming soon!")
        
        st.markdown("---")
        
        st.subheader("🎯 Quick Templates")
        
        templates = [
            "Basic Cosmetics Testing",
            "FDA Compliance Package",
            "EU Regulatory Testing",
            "Luxury Brand Protocol",
            "Sensitive Skin Products"
        ]
        
        for template in templates:
            if st.button(template, use_container_width=True):
                st.info(f"Loading {template} template...")
        
        st.markdown("---")
        
