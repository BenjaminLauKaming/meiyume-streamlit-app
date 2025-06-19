# 2D CAD Drawing Analyzer

This project uses Google's Gemini 1.5 Pro model to analyze 2D CAD drawings from a PDF file. It extracts dimensional data for each part, identifies parts, and performs a compatibility analysis to find mating dimensions between parts.

## Prerequisites

Before you begin, you need to have the following installed on your system:

1.  **Python 3.8+**
2.  **Poppler**: This is a PDF rendering library required for converting PDF pages to images.

    -   **On macOS (using Homebrew):**
        ```bash
        brew install poppler
        ```

    -   **On Debian/Ubuntu:**
        ```bash
        sudo apt-get update && sudo apt-get install -y poppler-utils
        ```
    -   **On Windows:**
        You can download Poppler for Windows and add its `bin` directory to your system's PATH.

## Setup

1.  **Clone the repository or download the files.**

2.  **Create a virtual environment (recommended):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```

3.  **Install the required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API Key:**
    You need a Google Generative AI API key.

    -   Create a new file named `.env` in the root of the project.
    -   Add your API key to this file in the following format:
        ```
        # .env
        GOOGLE_API_KEY="YOUR_API_KEY_HERE"
        ```
    Replace `"YOUR_API_KEY_HERE"` with your actual API key.

## How to Run

1.  Place your multi-page CAD drawing PDF file in the project's root directory (or note its path).

2.  Run the `cad_analyzer.py` script from your terminal, providing the path to your PDF file as an argument.

    ```bash
    python cad_analyzer.py /path/to/your/drawing.pdf
    ```

    For example, if your file is named `perfume_bottle.pdf` and is in the same directory:
    ```bash
    python cad_analyzer.py perfume_bottle.pdf
    ```

3.  **Specify an output directory (optional):**
    By default, all outputs are saved to a directory named `cad_analysis_output`. You can specify a different directory using the `--output_dir` flag.
    ```bash
    python cad_analyzer.py your_drawing.pdf --output_dir my_results
    ```

## Output

The script will generate a new directory (e.g., `cad_analysis_output`) containing:
-   A `pages/` subdirectory with one PNG image for each page of the PDF.
-   `extracted_dimensions.json`: A JSON file containing the structured dimensional data for each identified part.
-   `compatibility_analysis.json`: A JSON file listing all potential contact pairs between parts and their fit status. 