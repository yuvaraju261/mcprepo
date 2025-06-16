from flask import Flask, request, jsonify, send_file
import re
import dns.resolver
from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse
import logging
import pandas as pd
import PyPDF2
import pdfplumber
import tabula
import io
import os
from datetime import datetime
import tempfile

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailValidator:
    def __init__(self):
        # Comprehensive email regex pattern
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
        
        # Common disposable email domains
        self.disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'yopmail.com', 'temp-mail.org'
        }
    
    def validate_format(self, email):
        """Basic format validation using regex"""
        return bool(self.email_pattern.match(email))
    
    def validate_domain(self, email):
        """Check if domain has MX record"""
        try:
            domain = email.split('@')[1]
            dns.resolver.resolve(domain, 'MX')
            return True
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, Exception):
            return False
    
    def is_disposable(self, email):
        """Check if email is from a disposable email provider"""
        domain = email.split('@')[1].lower()
        return domain in self.disposable_domains
    
    def comprehensive_validate(self, email):
        """Comprehensive email validation using email-validator library"""
        try:
            # This performs RFC-compliant validation and DNS checking
            valid = validate_email(email)
            return True, valid.email
        except EmailNotValidError as e:
            return False, str(e)

class PDFToCSVConverter:
    def __init__(self):
        self.supported_methods = ['pdfplumber', 'tabula', 'pypdf2']
    
    def extract_text_pypdf2(self, pdf_file):
        """Extract text using PyPDF2"""
        try:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_data = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text.strip():
                    # Split text into lines and create basic structure
                    lines = [line.strip() for line in text.split('\n') if line.strip()]
                    for line in lines:
                        text_data.append({
                            'page': page_num + 1,
                            'content': line
                        })
            
            return pd.DataFrame(text_data)
        except Exception as e:
            raise Exception(f"PyPDF2 extraction failed: {str(e)}")
    
    def extract_tables_pdfplumber(self, pdf_file):
        """Extract tables using pdfplumber"""
        try:
            all_tables = []
            
            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    tables = page.extract_tables()
                    
                    if tables:
                        for table_num, table in enumerate(tables):
                            # Convert table to DataFrame
                            if table and len(table) > 0:
                                # Use first row as headers if it looks like headers
                                headers = table[0] if table[0] else [f'Column_{i}' for i in range(len(table[0]) if table else 0)]
                                data = table[1:] if len(table) > 1 else []
                                
                                if data:
                                    df = pd.DataFrame(data, columns=headers)
                                    df['page'] = page_num + 1
                                    df['table'] = table_num + 1
                                    all_tables.append(df)
                    else:
                        # If no tables, extract text
                        text = page.extract_text()
                        if text and text.strip():
                            lines = [line.strip() for line in text.split('\n') if line.strip()]
                            text_df = pd.DataFrame({
                                'content': lines,
                                'page': page_num + 1
                            })
                            all_tables.append(text_df)
            
            if all_tables:
                # Combine all tables/text
                result_df = pd.concat(all_tables, ignore_index=True, sort=False)
                return result_df
            else:
                return pd.DataFrame({'message': ['No extractable content found']})
                
        except Exception as e:
            raise Exception(f"PDFplumber extraction failed: {str(e)}")
    
    def extract_tables_tabula(self, pdf_file):
        """Extract tables using tabula-py"""
        try:
            # Save uploaded file temporarily for tabula
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                pdf_file.seek(0)
                tmp_file.write(pdf_file.read())
                tmp_file_path = tmp_file.name
            
            try:
                # Extract all tables from all pages
                tables = tabula.read_pdf(tmp_file_path, pages='all', multiple_tables=True)
                
                if tables:
                    all_tables = []
                    for i, table in enumerate(tables):
                        table['table_number'] = i + 1
                        all_tables.append(table)
                    
                    result_df = pd.concat(all_tables, ignore_index=True, sort=False)
                    return result_df
                else:
                    return pd.DataFrame({'message': ['No tables found in PDF']})
                    
            finally:
                # Clean up temporary file
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
                    
        except Exception as e:
            raise Exception(f"Tabula extraction failed: {str(e)}")
    
    def convert_pdf_to_csv(self, pdf_file, method='auto'):
        """Main conversion method"""
        if method == 'auto':
            # Try methods in order of preference
            methods_to_try = ['pdfplumber', 'tabula', 'pypdf2']
        else:
            methods_to_try = [method] if method in self.supported_methods else ['pdfplumber']
        
        last_error = None
        
        for extraction_method in methods_to_try:
            try:
                pdf_file.seek(0)  # Reset file pointer
                
                if extraction_method == 'pdfplumber':
                    df = self.extract_tables_pdfplumber(pdf_file)
                elif extraction_method == 'tabula':
                    df = self.extract_tables_tabula(pdf_file)
                elif extraction_method == 'pypdf2':
                    df = self.extract_text_pypdf2(pdf_file)
                
                if not df.empty:
                    return df, extraction_method
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Method {extraction_method} failed: {str(e)}")
                continue
        
        # If all methods failed
        raise Exception(f"All extraction methods failed. Last error: {str(last_error)}")

# Initialize components
validator = EmailValidator()
pdf_converter = PDFToCSVConverter()

@app.route('/convert-pdf-to-csv', methods=['POST'])
def convert_pdf_to_csv():
    """PDF to CSV conversion endpoint"""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({
                'error': 'No file uploaded',
                'success': False
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'success': False
            }), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({
                'error': 'File must be a PDF',
                'success': False
            }), 400
        
        # Get optional parameters
        method = request.form.get('method', 'auto')
        return_format = request.form.get('format', 'json')  # json or csv
        
        # Convert PDF to DataFrame
        df, used_method = pdf_converter.convert_pdf_to_csv(file, method)
        
        result = {
            'success': True,
            'method_used': used_method,
            'rows_extracted': len(df),
            'columns': list(df.columns),
            'timestamp': datetime.now().isoformat()
        }
        
        if return_format.lower() == 'csv':
            # Return CSV file
            output = io.StringIO()
            df.to_csv(output, index=False)
            output.seek(0)
            
            return send_file(
                io.BytesIO(output.getvalue().encode()),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f"{file.filename.rsplit('.', 1)[0]}_converted.csv"
            )
        else:
            # Return JSON with data
            result['data'] = df.to_dict('records')
            return jsonify(result), 200
            
    except Exception as e:
        logger.error(f"Error converting PDF to CSV: {str(e)}")
        return jsonify({
            'error': str(e),
            'success': False
        }), 500

@app.route('/pdf-to-csv-info', methods=['GET'])
def pdf_to_csv_info():
    """Get information about PDF to CSV conversion"""
    return jsonify({
        'service': 'PDF to CSV Converter',
        'supported_methods': pdf_converter.supported_methods,
        'usage': {
            'endpoint': '/convert-pdf-to-csv',
            'method': 'POST',
            'parameters': {
                'file': 'PDF file (required)',
                'method': 'Extraction method: auto, pdfplumber, tabula, pypdf2 (optional, default: auto)',
                'format': 'Response format: json or csv (optional, default: json)'
            },
            'example_curl': 'curl -X POST -F "file=@document.pdf" -F "method=auto" -F "format=json" http://localhost:5000/convert-pdf-to-csv'
        },
        'methods_description': {
            'pdfplumber': 'Best for structured tables and mixed content',
            'tabula': 'Specialized for table extraction',
            'pypdf2': 'Basic text extraction, fallback method',
            'auto': 'Tries all methods automatically'
        }
    }), 200

# Existing email validation endpoints
@app.route('/validate-email', methods=['POST'])
def validate_email_endpoint():
    """Email validation endpoint"""
    try:
        # Get email from request
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Email is required',
                'valid': False
            }), 400
        
        email = data['email'].strip()
        
        if not email:
            return jsonify({
                'error': 'Email cannot be empty',
                'valid': False
            }), 400
        
        # Perform validation checks
        result = {
            'email': email,
            'valid': False,
            'checks': {
                'format_valid': False,
                'domain_exists': False,
                'is_disposable': False,
                'comprehensive_valid': False
            },
            'errors': []
        }
        
        # Format validation
        result['checks']['format_valid'] = validator.validate_format(email)
        if not result['checks']['format_valid']:
            result['errors'].append('Invalid email format')
        
        # Domain validation (only if format is valid)
        if result['checks']['format_valid']:
            result['checks']['domain_exists'] = validator.validate_domain(email)
            if not result['checks']['domain_exists']:
                result['errors'].append('Domain does not exist or has no MX record')
            
            # Disposable email check
            result['checks']['is_disposable'] = validator.is_disposable(email)
            if result['checks']['is_disposable']:
                result['errors'].append('Disposable email addresses are not allowed')
            
            # Comprehensive validation
            is_valid, validation_result = validator.comprehensive_validate(email)
            result['checks']['comprehensive_valid'] = is_valid
            if not is_valid:
                result['errors'].append(f'Comprehensive validation failed: {validation_result}')
        
        # Overall validity
        result['valid'] = (
            result['checks']['format_valid'] and 
            result['checks']['domain_exists'] and 
            not result['checks']['is_disposable'] and
            result['checks']['comprehensive_valid']
        )
        
        # Log validation attempt
        logger.info(f"Email validation for {email}: {result['valid']}")
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error validating email: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'valid': False
        }), 500

@app.route('/validate-email-simple', methods=['POST'])
def validate_email_simple():
    """Simple email validation endpoint (format only)"""
    try:
        data = request.get_json()
        
        if not data or 'email' not in data:
            return jsonify({
                'error': 'Email is required',
                'valid': False
            }), 400
        
        email = data['email'].strip()
        is_valid = validator.validate_format(email)
        
        return jsonify({
            'email': email,
            'valid': is_valid,
            'message': 'Valid email format' if is_valid else 'Invalid email format'
        }), 200
        
    except Exception as e:
        logger.error(f"Error in simple validation: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'valid': False
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Multi-Purpose API',
        'version': '2.0.0',
        'features': ['Email Validation', 'PDF to CSV Conversion']
    }), 200

@app.route('/', methods=['GET'])
def index():
    """API documentation endpoint"""
    return jsonify({
        'service': 'Multi-Purpose API',
        'version': '2.0.0',
        'endpoints': {
            'POST /validate-email': 'Comprehensive email validation',
            'POST /validate-email-simple': 'Simple format validation',
            'POST /convert-pdf-to-csv': 'Convert PDF to CSV',
            'GET /pdf-to-csv-info': 'PDF conversion information',
            'GET /health': 'Health check',
            'GET /': 'API documentation'
        },
        'features': {
            'email_validation': {
                'format_validation': True,
                'domain_verification': True,
                'disposable_email_detection': True,
                'comprehensive_validation': True
            },
            'pdf_conversion': {
                'supported_formats': ['PDF'],
                'output_formats': ['CSV', 'JSON'],
                'extraction_methods': ['pdfplumber', 'tabula', 'pypdf2', 'auto'],
                'table_extraction': True,
                'text_extraction': True
            }
        },
        'usage_examples': {
            'email_validation': {
                'endpoint': '/validate-email',
                'method': 'POST',
                'body': {'email': 'user@example.com'},
                'response': {
                    'email': 'user@example.com',
                    'valid': True,
                    'checks': {
                        'format_valid': True,
                        'domain_exists': True,
                        'is_disposable': False,
                        'comprehensive_valid': True
                    },
                    'errors': []
                }
            },
            'pdf_conversion': {
                'endpoint': '/convert-pdf-to-csv',
                'method': 'POST',
                'content_type': 'multipart/form-data',
                'parameters': {
                    'file': 'PDF file',
                    'method': 'auto (optional)',
                    'format': 'json (optional)'
                }
            }
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)