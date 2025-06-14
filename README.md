# seace-contract-ocr-bow

## Overview
This project automates the process of downloading PDF contracts from a public source, converting them to images, extracting text using OCR (Optical Character Recognition), and transforming the extracted text into a structured format for further analysis. It is designed for large-scale document processing and text mining tasks.

## Features
- **Automated PDF Download:** Fetches contract PDFs from a list of URLs.
- **PDF to Image Conversion:** Converts each page of the PDF to an image using Poppler.
- **OCR Text Extraction:** Uses Tesseract OCR to extract text from images.
- **Text Structuring:** Processes and structures the extracted text for downstream analysis.
- **Batch Processing:** Handles large numbers of files efficiently.

## Folder Structure
- `src/` – Main Python scripts.
- `data/` – Input data files (e.g., Excel, CSV, TXT).
- `pdf/` – Downloaded PDF files.
- `text/` – Output text files from OCR.
- `temp/` – Temporary image files used during processing.

## Installation
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/conosce-pdf-ocr-bow.git
   cd conosce-pdf-ocr-bow
   ```

2. Set up the docker image:
   ```sh
   docker build -t contract-ocr:latest -f .devcontainer/Dockerfile .
   docker run -dit --name contract-ocr-dev -v "$repopath:/workspace" -w /workspace contract-ocr:latest
   ```

## Usage
1. Place your input data files (e.g., Excel with contract URLs) in the `data/` directory.
2. Run the main script:
   ```sh
   python src/notebook.ipynb
   ```
3. The script will:
   - Download missing PDFs to `pdf/`
   - Convert PDFs to images in `temp/`
   - Extract text to `text/`
   - Output structured data in `data/`

## Notes
- Ensure the paths in the script match your folder structure.
- For large-scale processing, monitor disk space in `temp/` and `text/`.
