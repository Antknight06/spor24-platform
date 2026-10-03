#!/usr/bin/env python
"""
Email validation utility for checking if email addresses actually exist
"""

import re
import socket
import smtplib
import dns.resolver
from typing import Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmailValidator:
    """Email validation class that checks if email addresses actually exist"""
    
    def __init__(self):
        self.timeout = 10  # seconds
        
    def is_valid_format(self, email: str) -> bool:
        """Check if email has valid format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_mx_record(self, domain: str) -> str:
        """Get MX record for domain"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            # Get the MX record with lowest preference (highest priority)
            mx_record = min(mx_records, key=lambda r: r.preference)
            return str(mx_record.exchange).rstrip('.')
        except Exception as e:
            logger.error(f"Error getting MX record for {domain}: {e}")
            return None
    
    def verify_email_smtp(self, email: str) -> Tuple[bool, str]:
        """
        Simplified email verification focusing on domain validation
        Returns (is_valid, message)
        """
        try:
            if not self.is_valid_format(email):
                return False, "Geçersiz email formatı"
            
            domain = email.split('@')[1]
            mx_server = self.get_mx_record(domain)
            
            if not mx_server:
                return False, "Email sunucusu bulunamadı - lütfen geçerli bir email giriniz"
            
            # If MX record exists, consider it valid
            # SMTP verification is often blocked, so we rely on MX record existence
            return True, "Email geçerli"
                
        except Exception as e:
            logger.error(f"Error verifying email {email}: {e}")
            # For unknown errors, be more strict
            return False, "Email doğrulanamadı - lütfen geçerli bir email giriniz"
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """
        Main validation method with improved error detection
        Returns (is_valid, message)
        """
        # First check format
        if not self.is_valid_format(email):
            return False, "Lütfen geçerli bir email formatı giriniz"
        
        # Extract domain
        domain = email.split('@')[1].lower()
        
        # Check for common invalid domains
        invalid_domains = [
            'example.com', 'test.com', 'invalid.com', 'fake.com',
            'dummy.com', 'sample.com', 'placeholder.com'
        ]
        
        if domain in invalid_domains:
            return False, "Lütfen geçerli bir email giriniz"
        
        # Check for common disposable email domains
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'temp-mail.org', 'throwaway.email',
            'yopmail.com', 'tempail.com', 'getnada.com'
        ]
        
        if domain in disposable_domains:
            return False, "Geçici email adresleri kabul edilmez"
        
        # Check for obviously fake patterns
        fake_patterns = ['nomail', 'noemail', 'fakeemail', 'testemail']
        local_part = email.split('@')[0].lower()
        
        if any(pattern in local_part for pattern in fake_patterns):
            return False, "Lütfen geçerli bir email giriniz"
        
        # Verify domain has MX record (simplified approach)
        return self.verify_email_smtp(email)

# Global validator instance
email_validator = EmailValidator()