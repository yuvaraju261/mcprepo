from flask import Flask, request, jsonify
import re
import dns.resolver
from email_validator import validate_email, EmailNotValidError
from urllib.parse import urlparse
import logging

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

# Initialize validator
validator = EmailValidator()

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
        'service': 'Email Validation API',
        'version': '1.0.0'
    }), 200

@app.route('/', methods=['GET'])
def index():
    """API documentation endpoint"""
    return jsonify({
        'service': 'Email Validation API',
        'version': '1.0.0',
        'endpoints': {
            'POST /validate-email': 'Comprehensive email validation',
            'POST /validate-email-simple': 'Simple format validation',
            'GET /health': 'Health check',
            'GET /': 'API documentation'
        },
        'usage': {
            'validate-email': {
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
            }
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)