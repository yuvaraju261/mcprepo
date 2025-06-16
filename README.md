# PDF to CSV Converter API

A comprehensive Flask-based API service that provides both email validation and PDF to CSV conversion functionality.

## Features

### Email Validation
- Format validation using regex
- Domain existence verification via DNS MX records
- Disposable email detection
- Comprehensive RFC-compliant validation

### PDF to CSV Conversion
- Multiple extraction methods: PDFplumber, Tabula, PyPDF2
- Automatic method selection
- Support for both tabular and text data
- JSON and CSV output formats
- Batch processing capabilities

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yuvaraju261/mcprepo.git
cd mcprepo
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

## API Endpoints

### 1. PDF to CSV Conversion

#### POST /convert-pdf-to-csv
Convert PDF files to CSV format with multiple extraction methods.

**Parameters:**
- `file`: PDF file (required)
- `method`: Extraction method - `auto`, `pdfplumber`, `tabula`, `pypdf2` (optional, default: `auto`)
- `format`: Response format - `json` or `csv` (optional, default: `json`)

**Example using curl:**
```bash
# Get JSON response
curl -X POST -F "file=@document.pdf" -F "method=auto" -F "format=json" http://localhost:5000/convert-pdf-to-csv

# Download CSV file
curl -X POST -F "file=@document.pdf" -F "format=csv" http://localhost:5000/convert-pdf-to-csv -o output.csv
```

**Example using Python requests:**
```python
import requests

# Upload PDF and get JSON response
with open('document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:5000/convert-pdf-to-csv',
        files={'file': f},
        data={'method': 'auto', 'format': 'json'}
    )
    
result = response.json()
print(f"Extracted {result['rows_extracted']} rows using {result['method_used']}")
```

#### GET /pdf-to-csv-info
Get information about PDF conversion capabilities and usage.

### 2. Email Validation

#### POST /validate-email
Comprehensive email validation with multiple checks.

**Request body:**
```json
{
    "email": "user@example.com"
}
```

**Response:**
```json
{
    "email": "user@example.com",
    "valid": true,
    "checks": {
        "format_valid": true,
        "domain_exists": true,
        "is_disposable": false,
        "comprehensive_valid": true
    },
    "errors": []
}
```

#### POST /validate-email-simple
Simple format-only email validation.

### 3. Utility Endpoints

#### GET /health
Health check endpoint.

#### GET /
API documentation and usage information.

## PDF Extraction Methods

### 1. PDFplumber (Recommended)
- **Best for:** Structured tables and mixed content
- **Strengths:** Excellent table detection, handles complex layouts
- **Use case:** Financial reports, data sheets, structured documents

### 2. Tabula
- **Best for:** Table-heavy documents
- **Strengths:** Specialized table extraction, handles complex table structures
- **Use case:** Scientific papers, statistical reports, tabular data

### 3. PyPDF2
- **Best for:** Simple text extraction
- **Strengths:** Reliable text extraction, lightweight
- **Use case:** Text documents, simple reports, fallback method

### 4. Auto Mode
- **Best for:** General use
- **Behavior:** Tries methods in order: pdfplumber → tabula → pypdf2
- **Use case:** When you're unsure about document structure

## Error Handling

The API provides comprehensive error handling:

- **400 Bad Request:** Missing file, invalid file format, empty file
- **500 Internal Server Error:** Processing errors, extraction failures

Example error response:
```json
{
    "error": "File must be a PDF",
    "success": false
}
```

## Response Formats

### JSON Response
```json
{
    "success": true,
    "method_used": "pdfplumber",
    "rows_extracted": 150,
    "columns": ["Name", "Age", "City", "page", "table"],
    "timestamp": "2025-06-16T16:11:56",
    "data": [
        {"Name": "John", "Age": "30", "City": "NYC", "page": 1, "table": 1},
        {"Name": "Jane", "Age": "25", "City": "LA", "page": 1, "table": 1}
    ]
}
```

### CSV Response
Direct CSV download with appropriate headers and filename.

## Deployment

### Local Development
```bash
python app.py
```
The API will be available at `http://localhost:5000`

### Production Deployment
Use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Java for tabula-py
RUN apt-get update && apt-get install -y default-jdk

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## Dependencies

- **Flask**: Web framework
- **pandas**: Data manipulation
- **pdfplumber**: PDF table extraction
- **tabula-py**: Advanced table extraction
- **PyPDF2**: Basic PDF processing
- **email-validator**: Email validation
- **dnspython**: DNS resolution

## Performance Considerations

- **File Size**: Recommended maximum 50MB per PDF
- **Processing Time**: Varies by document complexity (1-30 seconds typical)
- **Memory Usage**: Approximately 2-3x file size during processing
- **Concurrent Requests**: Limit concurrent PDF processing based on server resources

## Troubleshooting

### Common Issues

1. **Tabula fails to extract tables:**
   - Ensure Java is installed (`java -version`)
   - Try alternative methods: `pdfplumber` or `pypdf2`

2. **Empty extraction results:**
   - PDF might be image-based (scanned document)
   - Try OCR preprocessing with tools like Tesseract

3. **Memory errors:**
   - Reduce file size or split large PDFs
   - Increase server memory allocation

### Logging
The application logs all operations. Check logs for detailed error information:
```bash
tail -f app.log
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and support:
- Create an issue on GitHub
- Check the API documentation at `/` endpoint
- Review logs for detailed error information