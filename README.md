# Conosce PDF OCR BOW

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

2. Install the required Python packages:
   ```sh
   pip install -r requirements.txt
   ```

3. Make sure you have [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and [Poppler](https://poppler.freedesktop.org/) installed on your system.

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
