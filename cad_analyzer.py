import os
import json
import argparse
import google.generativeai as genai
from pdf2image import convert_from_path
from dotenv import load_dotenv
from PIL import Image
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def convert_pdf_to_images(pdf_path, output_folder):
    """
    Converts a PDF file to a list of PIL Images.
    NOTE: This function requires the poppler utility to be installed on your system.
    - macOS: brew install poppler
    - Debian/Ubuntu: sudo apt-get install poppler-utils
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    logging.info(f"Converting PDF '{pdf_path}' to images...")
    try:
        images = convert_from_path(pdf_path, dpi=300)
        image_paths = []
        for i, image in enumerate(images):
            image_path = os.path.join(output_folder, f"page_{i+1}.png")
            image.save(image_path, "PNG")
            image_paths.append(image_path)
        logging.info(f"Successfully converted PDF to {len(image_paths)} images in '{output_folder}'.")
        return image_paths
    except Exception as e:
        logging.error(f"Failed to convert PDF. Make sure poppler is installed and in your PATH. Error: {e}")
        return []

def get_gemini_prompt():
    """Returns the detailed prompt for the Gemini API call."""
    return """
    You are an expert AI assistant specializing in analyzing 2D CAD drawings.
    Your task is to analyze the provided images of a multi-page 2D CAD drawing.

    1. Identify all unique parts. A single part may be detailed across multiple pages.
    Group all drawings and views for the same part together. If a part name is not explicitly
    stated, infer a logical name or use "Unknown Part #[n]".

    2. For each part, extract all dimensional data with the highest precision.
    The output must be a JSON object containing a list of parts. Each part object should have the following structure:
    {
      "part_name": "...",
      "pages": [...],
      "dimensions": [
        {
          "feature": "...",
          "value": ...,
          "tolerance": "...",
          "unit": "...",
          "type": "interior" or "exterior",
          "dimension_type": "radius", "diameter", or "length",
          "is_critical_dimension": true or false
        },
        ...
      ]
    }

    Here are the rules for extraction:
    - "feature": A clear description (e.g., "Inner diameter of socket").
    - "value": The nominal dimension value as a float.
    - "tolerance": The tolerance as a string (e.g., "±0.1"). If none, use null.
    - "unit": The unit of measurement (e.g., "mm"). If not specified, assume "mm" and flag it in your assumptions.
    - "type": Classify as "interior" (e.g., hole diameter) or "exterior" (e.g., outer wall).
    - "dimension_type": "radius" (starts with R), "diameter" (starts with Ø), or "length" (for linear dimensions).
    - "is_critical_dimension": `true` if the dimension is enclosed in a rectangular box, otherwise `false`.

    3. After your analysis, provide a clear list of any assumptions you made (e.g., inferred part names, assumed units).

    Please return ONLY the JSON data structure. Do not include any explanatory text before or after the JSON object.
    """

def analyze_images_with_gemini(image_paths, api_key):
    """
    Analyzes a list of image files using the Gemini Pro Vision model.
    """
    if not api_key:
        raise ValueError("GOOGLE_API_KEY is not set. Please set it in your .env file.")

    genai.configure(api_key=api_key)
    
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    prompt = get_gemini_prompt()
    
    image_parts = []
    for img_path in image_paths:
        try:
            img = Image.open(img_path)
            image_parts.append(img)
        except IOError:
            logging.error(f"Could not open image file: {img_path}")
            return None

    logging.info(f"Sending {len(image_parts)} images to Gemini for analysis...")
    
    try:
        response = model.generate_content([prompt] + image_parts)
        # Clean the response to extract only the JSON part
        cleaned_response_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned_response_text)
    except Exception as e:
        logging.error(f"An error occurred during Gemini API call: {e}")
        logging.error(f"Raw response text: {response.text if 'response' in locals() else 'No response received'}")
        return None

def parse_tolerance(value, tolerance_str):
    """Parses a tolerance string '±value' and returns min and max values."""
    if tolerance_str is None or "±" not in tolerance_str:
        return value, value
    
    try:
        tol_val = float(tolerance_str.replace("±", "").strip())
        return value - tol_val, value + tol_val
    except (ValueError, TypeError):
        return value, value

def analyze_compatibility(parts_data):
    """
    Analyzes dimensional compatibility between pairs of parts.
    """
    if not parts_data or 'parts' not in parts_data:
        logging.warning("Parts data is empty or invalid. Skipping compatibility analysis.")
        return []

    parts = parts_data['parts']
    contact_pairs = []

    logging.info("Analyzing compatibility between parts...")
    for i in range(len(parts)):
        for j in range(i + 1, len(parts)):
            part_a = parts[i]
            part_b = parts[j]

            for dim_a in part_a.get("dimensions", []):
                for dim_b in part_b.get("dimensions", []):
                    # Look for interior/exterior pairs of the same dimension type
                    if dim_a.get("type") == "interior" and dim_b.get("type") == "exterior" and dim_a.get("dimension_type") == dim_b.get("dimension_type"):
                        
                        val_a = dim_a.get("value")
                        val_b = dim_b.get("value")
                        
                        # Check if nominal values are close (e.g., within 10%)
                        if val_a is not None and val_b is not None and val_b != 0 and abs(val_a - val_b) / val_b < 0.1:
                            min_a, max_a = parse_tolerance(val_a, dim_a.get("tolerance"))
                            min_b, max_b = parse_tolerance(val_b, dim_b.get("tolerance"))
                            
                            fit_status = "ambiguous"
                            # Overlap condition: max_a >= min_b and min_a <= max_b
                            if max_a >= min_b and min_a <= max_b:
                                # Clearance fit: Hole is larger than shaft
                                if min_a > max_b:
                                    fit_status = "likely compatible (clearance fit)"
                                # Interference fit: Hole is smaller than shaft
                                elif max_a < min_b:
                                    fit_status = "likely compatible (interference fit)"
                                else:
                                    fit_status = "likely compatible (transition fit)"
                            else:
                                fit_status = "incompatible"

                            contact_pairs.append({
                                "contact_pair": {
                                    "part_a": part_a.get("part_name"),
                                    "feature_a": dim_a.get("feature"),
                                    "value_a": val_a,
                                    "tolerance_a": dim_a.get("tolerance"),
                                    "type_a": "interior",
                                    "part_b": part_b.get("part_name"),
                                    "feature_b": dim_b.get("feature"),
                                    "value_b": val_b,
                                    "tolerance_b": dim_b.get("tolerance"),
                                    "type_b": "exterior",
                                    "fit_status": fit_status
                                }
                            })
    
    logging.info(f"Found {len(contact_pairs)} potential contact pairs.")
    return contact_pairs

def main():
    """Main function to orchestrate the CAD analysis."""
    parser = argparse.ArgumentParser(description="Analyze 2D CAD drawings from a PDF using Gemini.")
    parser.add_argument("pdf_path", type=str, help="Path to the input PDF file.")
    parser.add_argument("--output_dir", type=str, default="cad_analysis_output", help="Directory to save output files.")
    args = parser.parse_args()

    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        logging.error("API key for Google not found. Please create a .env file with GOOGLE_API_KEY=<your-key>.")
        return
        
    image_paths = convert_pdf_to_images(args.pdf_path, os.path.join(args.output_dir, "pages"))
    if not image_paths:
        logging.error("Stopping execution due to image conversion failure.")
        return

    extracted_data = analyze_images_with_gemini(image_paths, api_key)
    
    if extracted_data:
        # Save extracted data
        extracted_data_path = os.path.join(args.output_dir, "extracted_dimensions.json")
        with open(extracted_data_path, 'w') as f:
            json.dump(extracted_data, f, indent=2)
        logging.info(f"Extracted dimensions saved to '{extracted_data_path}'.")

        # Perform and save compatibility analysis
        contact_pairs = analyze_compatibility(extracted_data)
        compatibility_path = os.path.join(args.output_dir, "compatibility_analysis.json")
        with open(compatibility_path, 'w') as f:
            json.dump(contact_pairs, f, indent=2)
        logging.info(f"Compatibility analysis saved to '{compatibility_path}'.")
    else:
        logging.error("Failed to get structured data from Gemini.")

if __name__ == "__main__":
    main() 