import unittest
import json
from app import app, EmailValidator

class TestEmailValidator(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.validator = EmailValidator()
    
    def test_valid_email_format(self):
        """Test valid email formats"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.co.uk',
            'user+tag@example.org',
            'user123@test-domain.com'
        ]
        
        for email in valid_emails:
            with self.subTest(email=email):
                self.assertTrue(self.validator.validate_format(email))
    
    def test_invalid_email_format(self):
        """Test invalid email formats"""
        invalid_emails = [
            'invalid-email',
            '@example.com',
            'user@',
            'user..name@example.com',
            'user@.com',
            'user@domain.',
            ''
        ]
        
        for email in invalid_emails:
            with self.subTest(email=email):
                self.assertFalse(self.validator.validate_format(email))
    
    def test_disposable_email_detection(self):
        """Test disposable email detection"""
        disposable_emails = [
            'test@10minutemail.com',
            'user@tempmail.org',
            'temp@guerrillamail.com'
        ]
        
        for email in disposable_emails:
            with self.subTest(email=email):
                self.assertTrue(self.validator.is_disposable(email))
    
    def test_validate_email_endpoint_valid(self):
        """Test the validate-email endpoint with valid email"""
        response = self.app.post('/validate-email',
                               data=json.dumps({'email': 'test@gmail.com'}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('email', data)
        self.assertIn('valid', data)
        self.assertIn('checks', data)
    
    def test_validate_email_endpoint_invalid(self):
        """Test the validate-email endpoint with invalid email"""
        response = self.app.post('/validate-email',
                               data=json.dumps({'email': 'invalid-email'}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertFalse(data['valid'])
        self.assertGreater(len(data['errors']), 0)
    
    def test_validate_email_endpoint_missing_email(self):
        """Test the validate-email endpoint without email"""
        response = self.app.post('/validate-email',
                               data=json.dumps({}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertFalse(data['valid'])
        self.assertIn('error', data)
    
    def test_simple_validation_endpoint(self):
        """Test the simple validation endpoint"""
        response = self.app.post('/validate-email-simple',
                               data=json.dumps({'email': 'test@example.com'}),
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('email', data)
        self.assertIn('valid', data)
        self.assertIn('message', data)
    
    def test_health_endpoint(self):
        """Test the health check endpoint"""
        response = self.app.get('/health')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_index_endpoint(self):
        """Test the index/documentation endpoint"""
        response = self.app.get('/')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('service', data)
        self.assertIn('endpoints', data)

if __name__ == '__main__':
    unittest.main()