"""
Certificate Schemas
Pydantic schemas for certificate management
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from ..models.certificate import CertificateType


class CertificateBase(BaseModel):
    """Base certificate schema"""
    name: str = Field(..., min_length=1, max_length=255)
    subject_cn: str = Field(..., min_length=1, max_length=255)
    subject_o: Optional[str] = None
    subject_ou: Optional[str] = None
    subject_c: Optional[str] = None
    subject_st: Optional[str] = None
    subject_l: Optional[str] = None
    subject_email: Optional[str] = None


class CertificateCreate(CertificateBase):
    """Schema for creating certificate"""
    san_dns_names: Optional[List[str]] = None
    san_ip_addresses: Optional[List[str]] = None
    san_emails: Optional[List[str]] = None
    algorithm: str = Field(default='RSA', regex='^(RSA|ECDSA|Ed25519)$')
    key_size: int = Field(default=2048, ge=2048, le=4096)
    validity_days: Optional[int] = Field(None, ge=1, le=3650)
    certificate_type: CertificateType = CertificateType.SERVER
    auto_renew: bool = False

    @validator('key_size')
    def validate_key_size(cls, v, values):
        algorithm = values.get('algorithm', 'RSA')
        if algorithm == 'RSA' and v not in [2048, 4096]:
            raise ValueError('RSA key size must be 2048 or 4096')
        if algorithm == 'ECDSA' and v not in [256, 384, 521]:
            raise ValueError('ECDSA key size must be 256, 384, or 521')
        return v


class CertificateResponse(CertificateBase):
    """Schema for certificate response"""
    id: int
    serial_number: str
    type: CertificateType
    algorithm: str
    key_size: int
    is_active: bool
    is_revoked: bool
    not_before: datetime
    not_after: datetime
    sha256_fingerprint: str
    days_until_expiry: int
    needs_renewal: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CertificateWithKey(CertificateResponse):
    """Schema for certificate with private key (only shown on creation)"""
    certificate_pem: str
    private_key_pem: str
    public_key_pem: str


class CertificateVerify(BaseModel):
    """Schema for certificate verification"""
    certificate_pem: str

    class Config:
        schema_extra = {
            "example": {
                "certificate_pem": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----"
            }
        }


class CertificateVerifyResponse(BaseModel):
    """Schema for certificate verification response"""
    valid: bool
    is_expired: bool
    is_not_yet_valid: bool
    is_signed_by_ca: Optional[bool] = None
    is_revoked: bool
    subject: dict
    dns_names: List[str]
    ip_addresses: List[str]
    emails: List[str]
    not_before: str
    not_after: str
    days_until_expiry: int


class CSRCreate(BaseModel):
    """Schema for creating certificate signing request"""
    name: str = Field(..., min_length=1, max_length=255)
    subject_cn: str = Field(..., min_length=1, max_length=255)
    subject_o: Optional[str] = None
    subject_ou: Optional[str] = None
    subject_c: Optional[str] = None
    subject_st: Optional[str] = None
    subject_l: Optional[str] = None
    subject_email: Optional[str] = None
    san_dns_names: Optional[List[str]] = None
    san_ip_addresses: Optional[List[str]] = None
    san_emails: Optional[List[str]] = None
    algorithm: str = Field(default='RSA', regex='^(RSA|ECDSA)$')
    key_size: int = Field(default=2048, ge=2048, le=4096)


class CSRResponse(BaseModel):
    """Schema for CSR response"""
    request_id: str
    csr_pem: str
    private_key_pem: str


class CertificateRequestResponse(BaseModel):
    """Schema for certificate request"""
    id: int
    request_id: str
    subject_cn: str
    status: str
    created_at: datetime
    algorithm: str
    key_size: int
