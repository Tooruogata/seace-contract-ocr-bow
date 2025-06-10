FROM python:3.13-slim

# Install system dependencies for Tesseract and Poppler
RUN apt-get update && \
    apt-get install -y tesseract-ocr poppler-utils libgl1-mesa-glx && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set default working directory (important for Dev Containers)
WORKDIR /workspace

# Copy the requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt


# Default command (optional)
CMD ["bash"]