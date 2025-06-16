# Email Validation API

A robust Python Flask API for comprehensive email validation.

## Features

- **Format Validation**: Validates email format using regex patterns
- **Domain Validation**: Checks if the domain exists and has MX records
- **Disposable Email Detection**: Identifies and blocks disposable email addresses
- **Comprehensive Validation**: Uses RFC-compliant validation with the `email-validator` library
- **Multiple Endpoints**: Both comprehensive and simple validation options
- **Health Check**: Built-in health monitoring endpoint
- **Detailed Response**: Provides breakdown of all validation checks

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

The API will be available at `http://localhost:5000`

## API Endpoints

### 1. Comprehensive Email Validation
**POST** `/validate-email`

Validates email with multiple checks including format, domain existence, disposable email detection, and RFC compliance.

**Request:**
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

### 2. Simple Email Validation
**POST** `/validate-email-simple`

Performs basic format validation only.

**Request:**
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
  "message": "Valid email format"
}
```

### 3. Health Check
**GET** `/health`

Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "service": "Email Validation API",
  "version": "1.0.0"
}
```

### 4. API Documentation
**GET** `/`

Returns API documentation and usage examples.

## Usage Examples

### Using cURL

```bash
# Comprehensive validation
curl -X POST http://localhost:5000/validate-email \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com"}'

# Simple validation
curl -X POST http://localhost:5000/validate-email-simple \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com"}'

# Health check
curl http://localhost:5000/health
```

### Using Python requests

```python
import requests

# Comprehensive validation
response = requests.post(
    'http://localhost:5000/validate-email',
    json={'email': 'test@gmail.com'}
)
print(response.json())

# Simple validation
response = requests.post(
    'http://localhost:5000/validate-email-simple',
    json={'email': 'test@gmail.com'}
)
print(response.json())
```

## Validation Features

### Format Validation
- Uses regex pattern to validate basic email structure
- Checks for valid characters, @ symbol, and domain format

### Domain Validation
- Performs DNS lookup to verify domain exists
- Checks for MX (Mail Exchange) records

### Disposable Email Detection
- Maintains a list of known disposable email providers
- Blocks common temporary email services

### Comprehensive Validation
- Uses the `email-validator` library for RFC-compliant validation
- Performs internationalized domain name (IDN) validation
- Checks for deliverability indicators

## Error Handling

The API provides detailed error messages for various validation failures:

- **Invalid email format**: Basic format validation failed
- **Domain does not exist**: Domain has no MX records or doesn't exist
- **Disposable email**: Email is from a disposable email provider
- **Comprehensive validation failed**: RFC compliance or other advanced checks failed

## Docker Support

Create a `Dockerfile` for containerized deployment:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]
```

Build and run:
```bash
docker build -t email-validator .
docker run -p 5000:5000 email-validator
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the [MIT License](LICENSE).