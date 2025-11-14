#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Security Hardening Implementation

Implements security enhancements for the multi-source data integration:
1. Input validation
2. API rate limiting
3. XSS protection
4. SQL injection prevention
5. Secure headers
6. Authentication/Authorization

Author: Claude Code
Version: 1.0
Date: 2025-11-10
"""

import re
import time
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from functools import wraps
from pathlib import Path


class SecurityError(Exception):
    """Custom security exception"""
    pass


class InputValidator:
    """Validate and sanitize user inputs"""

    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r'<script.*?>.*?</script>',  # XSS
        r'union\s+select',  # SQL injection
        r'../',  # Path traversal
        r'[\x00-\x1f\x7f-\x9f]',  # Control characters
    ]

    def __init__(self):
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.DANGEROUS_PATTERNS
        ]

    def validate_date(self, date_str: str) -> bool:
        """Validate date string format (YYYY-MM-DD)"""
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if not re.match(pattern, date_str):
            return False

        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def validate_symbol(self, symbol: str) -> bool:
        """Validate stock symbol format (e.g., 0700.HK)"""
        pattern = r'^\d{4}\.HK$'
        return bool(re.match(pattern, symbol.upper()))

    def validate_source_name(self, source: str) -> bool:
        """Validate data source name"""
        valid_sources = ['visitor', 'property', 'gdp', 'retail', 'trade', 'hibor']
        return source.lower() in valid_sources

    def sanitize_input(self, input_str: str) -> str:
        """Sanitize input by removing dangerous characters"""
        # Remove null bytes and control characters
        sanitized = ''.join(
            c for c in input_str
            if ord(c) >= 32 or c in ['\n', '\r', '\t']
        )

        # Check for dangerous patterns
        for pattern in self.compiled_patterns:
            if pattern.search(sanitized):
                raise SecurityError(f"Dangerous pattern detected: {pattern.pattern}")

        return sanitized.strip()

    def validate_data_range(self, start_date: str, end_date: str) -> bool:
        """Validate date range (max 5 years)"""
        if not (self.validate_date(start_date) and self.validate_date(end_date)):
            return False

        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')

        if end < start:
            return False

        # Max range: 5 years
        if (end - start).days > 5 * 365:
            return False

        return True


class RateLimiter:
    """API rate limiter with sliding window"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(deque)

    def is_rate_limited(self, client_id: str) -> bool:
        """Check if client is rate limited"""
        now = time.time()
        window_start = now - self.window_seconds

        # Clean old requests
        client_requests = self.requests[client_id]
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()

        # Check limit
        if len(client_requests) >= self.max_requests:
            return True

        # Add current request
        client_requests.append(now)
        return False

    def get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client"""
        now = time.time()
        window_start = now - self.window_seconds

        client_requests = self.requests[client_id]
        # Clean old requests
        while client_requests and client_requests[0] < window_start:
            client_requests.popleft()

        return max(0, self.max_requests - len(client_requests))


class SecurityHeaders:
    """Generate secure HTTP headers"""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers"""
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https://data.gov.hk https://censtatd.gov.hk"
            ),
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }


class APISecurityMiddleware:
    """API security middleware"""

    def __init__(self):
        self.validator = InputValidator()
        self.rate_limiter = RateLimiter(max_requests=100, window_seconds=60)
        self.api_keys = {}  # In production, use secure storage

    def require_api_key(self, api_key: str, client_id: str) -> bool:
        """Validate API key"""
        if not api_key:
            return False

        # In production, verify against database or secure storage
        expected_key = self.api_keys.get(client_id)
        if not expected_key:
            return False

        # Use constant-time comparison
        return hmac.compare_digest(api_key, expected_key)

    def validate_request(self, request_data: Dict) -> Tuple[bool, str]:
        """Validate incoming request"""
        # Validate required fields
        required_fields = ['source', 'start_date', 'end_date']
        for field in required_fields:
            if field not in request_data:
                return False, f"Missing required field: {field}"

        # Validate data source
        if not self.validator.validate_source_name(request_data['source']):
            return False, f"Invalid data source: {request_data['source']}"

        # Validate date range
        if not self.validator.validate_data_range(
            request_data['start_date'],
            request_data['end_date']
        ):
            return False, "Invalid date range"

        # Sanitize inputs
        try:
            request_data['source'] = self.validator.sanitize_input(
                request_data['source']
            )
        except SecurityError as e:
            return False, str(e)

        return True, "Valid"


def secure_api_endpoint(max_requests: int = 100, window_seconds: int = 60):
    """
    Decorator to secure API endpoints

    Args:
        max_requests: Maximum requests per window
        window_seconds: Time window in seconds
    """
    rate_limiter = RateLimiter(max_requests, window_seconds)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get client ID (from request header or IP)
            client_id = kwargs.get('client_id', 'anonymous')

            # Check rate limit
            if rate_limiter.is_rate_limited(client_id):
                raise SecurityError(
                    f"Rate limit exceeded. Try again later. "
                    f"Remaining: {rate_limiter.get_remaining_requests(client_id)}"
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


class DataValidationError(Exception):
    """Data validation error"""
    pass


def validate_output_data(data: Dict) -> bool:
    """
    Validate output data for security issues

    Args:
        data: Data to validate

    Returns:
        True if valid

    Raises:
        DataValidationError: If validation fails
    """
    validator = InputValidator()

    # Check for required fields
    if not isinstance(data, dict):
        raise DataValidationError("Data must be a dictionary")

    # Validate numeric fields
    numeric_fields = ['value', 'growth', 'percentage']
    for field in numeric_fields:
        if field in data:
            try:
                float(data[field])
            except (ValueError, TypeError):
                raise DataValidationError(f"Invalid numeric value for {field}")

    # Check for injection patterns
    for key, value in data.items():
        if isinstance(value, str):
            try:
                validator.sanitize_input(value)
            except SecurityError as e:
                raise DataValidationError(f"Invalid value for {key}: {e}")

    return True


def generate_secure_config() -> Dict:
    """Generate secure configuration template"""
    return {
        'security': {
            'rate_limiting': {
                'enabled': True,
                'max_requests': 100,
                'window_seconds': 60,
                'burst_limit': 200
            },
            'input_validation': {
                'enabled': True,
                'sanitize_inputs': True,
                'max_input_length': 10000
            },
            'cors': {
                'enabled': True,
                'allowed_origins': [
                    'https://your-domain.com',
                    'https://localhost:8001'
                ],
                'allowed_methods': ['GET', 'POST'],
                'allowed_headers': ['Content-Type', 'Authorization', 'X-API-Key']
            },
            'headers': {
                'enable_security_headers': True,
                'enable_hsts': True,
                'enable_csp': True
            },
            'api_keys': {
                'require_auth': True,
                'key_rotation_days': 90,
                'max_key_age_days': 365
            }
        }
    }


def security_audit_checklist() -> List[str]:
    """Generate security audit checklist"""
    return [
        "[ ] Input validation implemented for all user inputs",
        "[ ] SQL injection prevention (use parameterized queries)",
        "[ ] XSS protection (sanitize output, use CSP)",
        "[ ] CSRF protection (use tokens)",
        "[ ] Rate limiting implemented",
        "[ ] API authentication/authorization",
        "[ ] Secure headers configured",
        "[ ] HTTPS enforced (SSL/TLS)",
        "[ ] Sensitive data encrypted at rest",
        "[ ] Error messages don't leak sensitive info",
        "[ ] API keys stored securely (not in code)",
        "[ ] Logging doesn't include sensitive data",
        "[ ] Regular security updates",
        "[ ] File upload validation",
        "[ ] Directory traversal prevention",
        "[ ] Command injection prevention",
        "[ ] XML external entity (XXE) prevention",
        "[ ] Security testing (penetration testing)",
        "[ ] Dependency vulnerability scanning",
        "[ ] Container security (if using Docker)"
    ]


def main():
    """Main entry point - demonstrate security features"""
    print("=" * 80)
    print("SECURITY HARDENING IMPLEMENTATION")
    print("=" * 80)

    # Test input validation
    print("\n1. Input Validation Tests:")
    validator = InputValidator()

    test_cases = [
        ("Visitor", "2020-01-01", "2023-12-31", True),
        ("visitor", "2020-01-01", "2023-12-31", True),
        ("invalid_source", "2020-01-01", "2023-12-31", False),
        ("visitor", "invalid-date", "2023-12-31", False),
        ("visitor", "2020-01-01", "2019-01-01", False),  # End before start
    ]

    for source, start, end, expected in test_cases:
        result = validator.validate_source_name(source) and \
                 validator.validate_date(start) and \
                 validator.validate_date(end) and \
                 validator.validate_data_range(start, end)
        status = "[PASS]" if result == expected else "[FAIL]"
        print(f"  {status} Source: {source}, Range: {start} to {end}")

    # Test rate limiting
    print("\n2. Rate Limiting Test:")
    rate_limiter = RateLimiter(max_requests=5, window_seconds=60)

    for i in range(7):
        is_limited = rate_limiter.is_rate_limited('test_client')
        status = "[LIMITED]" if is_limited else "[OK]"
        remaining = rate_limiter.get_remaining_requests('test_client')
        print(f"  {status} Request {i+1}, Remaining: {remaining}")

    # Test security headers
    print("\n3. Security Headers:")
    headers = SecurityHeaders.get_security_headers()
    for header, value in headers.items():
        print(f"  {header}: {value[:50]}...")

    # Test secure config
    print("\n4. Secure Configuration Generated:")
    config = generate_secure_config()
    print(f"  Rate limiting: {config['security']['rate_limiting']['enabled']}")
    print(f"  Input validation: {config['security']['input_validation']['enabled']}")

    # Security audit checklist
    print("\n5. Security Audit Checklist:")
    checklist = security_audit_checklist()
    for item in checklist[:10]:  # Show first 10
        print(f"  {item}")
    print(f"  ... and {len(checklist) - 10} more items")

    print("\n" + "=" * 80)
    print("Security hardening configuration complete!")
    print("=" * 80)

    # Save security config
    import json
    with open('security_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

    with open('SECURITY_AUDIT_CHECKLIST.md', 'w', encoding='utf-8') as f:
        f.write("# Security Audit Checklist\n\n")
        f.write("This checklist should be completed before production deployment.\n\n")
        for item in checklist:
            f.write(f"{item}\n")

    print("\nConfiguration files saved:")
    print("  - security_config.json")
    print("  - SECURITY_AUDIT_CHECKLIST.md")


if __name__ == '__main__':
    main()
