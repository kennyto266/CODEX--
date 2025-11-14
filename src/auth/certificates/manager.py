"""
Certificate Management System (T110)
Enterprise-grade PKI implementation with SSL/TLS certificate lifecycle management
"""

import json
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtensionOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519
from cryptography.hazmat.primitives.serialization import pkcs7
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ..core.config import AuthConfig
from ..core.security import SecurityManager
from ..models.certificate import Certificate, CertificateType, CertificateRequest
from ..models.security_event import SecurityEvent, SecurityEventType

logger = logging.getLogger("hk_quant_system.auth.certificates")


class CertificateManager:
    """
    Certificate Management System
    Handles PKI infrastructure, certificate creation, and lifecycle management
    """

    def __init__(self, config: AuthConfig, security: SecurityManager, db_session: Session):
        """
        Initialize certificate manager

        Args:
            config: Authentication configuration
            security: Security manager instance
            db_session: Database session
        """
        self.config = config
        self.security = security
        self.db = db_session
        self._ca_private_key = None
        self._ca_certificate = None
        self._load_or_create_ca()

    def _load_or_create_ca(self) -> None:
        """Load existing CA or create new self-signed CA"""
        try:
            # Try to load existing CA
            if os.path.exists(self.config.cert_ca_cert_path) and os.path.exists(self.config.cert_ca_key_path):
                with open(self.config.cert_ca_cert_path, 'rb') as f:
                    self._ca_certificate = x509.load_pem_x509_certificate(f.read())
                with open(self.config.cert_ca_key_path, 'rb') as f:
                    self._ca_private_key = serialization.load_pem_private_key(
                        f.read(),
                        password=None
                    )
                logger.info("Loaded existing CA certificate")
                return

            # Create new self-signed CA
            self._create_ca_certificate()
            logger.info("Created new self-signed CA certificate")

        except Exception as e:
            logger.error(f"Failed to load/create CA: {e}")
            # Create ephemeral CA for development
            self._create_ca_certificate()

    def _create_ca_certificate(self) -> None:
        """Create new self-signed CA certificate"""
        # Generate CA private key
        self._ca_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

        # Create CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, self.config.cert_country),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, self.config.cert_state),
            x509.NameAttribute(NameOID.LOCALITY_NAME, self.config.cert_city),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.config.cert_organization),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, self.config.cert_organizational_unit),
            x509.NameAttribute(NameOID.COMMON_NAME, "HK Quant System CA"),
        ])

        # Create certificate
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            self._ca_private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=3650)  # 10 years
        ).add_extension(
            x509.SubjectKeyIdentifier.from_public_key(self._ca_private_key.public_key()),
            critical=False,
        ).add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(self._ca_private_key.public_key()),
            critical=False,
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_cert_sign=True,
                crl_sign=True,
                key_encipherment=False,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).sign(self._ca_private_key, hashes.SHA256())

        self._ca_certificate = cert

        # Save CA certificate and key
        os.makedirs(os.path.dirname(self.config.cert_ca_cert_path), exist_ok=True)

        with open(self.config.cert_ca_cert_path, 'wb') as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))

        with open(self.config.cert_ca_key_path, 'wb') as f:
            f.write(self._ca_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))

    def generate_certificate(
        self,
        name: str,
        subject_cn: str,
        subject_o: Optional[str] = None,
        subject_ou: Optional[str] = None,
        subject_c: Optional[str] = None,
        subject_st: Optional[str] = None,
        subject_l: Optional[str] = None,
        subject_email: Optional[str] = None,
        san_dns_names: Optional[List[str]] = None,
        san_ip_addresses: Optional[List[str]] = None,
        san_emails: Optional[List[str]] = None,
        algorithm: str = 'RSA',
        key_size: int = 2048,
        validity_days: Optional[int] = None,
        certificate_type: CertificateType = CertificateType.SERVER,
        auto_renew: bool = False
    ) -> Dict[str, Any]:
        """
        Generate new certificate

        Args:
            name: Certificate name
            subject_cn: Common Name
            subject_o: Organization
            subject_ou: Organizational Unit
            subject_c: Country
            subject_st: State/Province
            subject_l: Locality
            subject_email: Email
            san_dns_names: DNS Subject Alternative Names
            san_ip_addresses: IP Address SANs
            san_emails: Email SANs
            algorithm: Key algorithm (RSA, ECDSA, Ed25519)
            key_size: Key size (2048, 4096 for RSA)
            validity_days: Certificate validity in days
            certificate_type: Type of certificate
            auto_renew: Enable auto-renewal

        Returns:
            Dictionary with certificate information
        """
        try:
            if validity_days is None:
                validity_days = self.config.cert_validity_days

            # Generate private key
            if algorithm.upper() == 'RSA':
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=key_size,
                )
            elif algorithm.upper() == 'ECDSA':
                private_key = ec.generate_private_key(ec.SECP256R1())
                key_size = 256
            elif algorithm.upper() == 'ED25519':
                private_key = ed25519.Ed25519PrivateKey.generate()
                key_size = 256
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            # Create subject
            subject_attributes = [
                x509.NameAttribute(NameOID.COMMON_NAME, subject_cn),
            ]

            if subject_o:
                subject_attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, subject_o))
            if subject_ou:
                subject_attributes.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, subject_ou))
            if subject_c:
                subject_attributes.append(x509.NameAttribute(NameOID.COUNTRY_NAME, subject_c))
            if subject_st:
                subject_attributes.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, subject_st))
            if subject_l:
                subject_attributes.append(x509.NameAttribute(NameOID.LOCALITY_NAME, subject_l))
            if subject_email:
                subject_attributes.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, subject_email))

            subject = x509.Name(subject_attributes)

            # Create SANs
            san_list = []
            if san_dns_names:
                san_list.append(
                    x509.SubjectAlternativeName([
                        x509.DNSName(name) for name in san_dns_names
                    ])
                )
            if san_ip_addresses:
                from ipaddress import ip_address
                for ip in san_ip_addresses:
                    try:
                        san_list.append(
                            x509.SubjectAlternativeName([
                                x509.IPAddress(ip_address(ip))
                            ])
                        )
                    except ValueError:
                        # Skip invalid IPs
                        pass
            if san_emails:
                san_list.append(
                    x509.SubjectAlternativeName([
                        x509.RFC822Name(email) for email in san_emails
                    ])
                )

            # Generate serial number
            serial_number = secrets.token_hex(16)

            # Build certificate
            cert_builder = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                self._ca_certificate.subject
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=validity_days)
            )

            # Add SANs
            for san in san_list:
                cert_builder = cert_builder.add_extension(san, critical=False)

            # Add key usage
            if certificate_type == CertificateType.SERVER:
                cert_builder = cert_builder.add_extension(
                    x509.KeyUsage(
                        digital_signature=True,
                        key_encipherment=True,
                        key_cert_sign=False,
                        crl_sign=False,
                        content_commitment=False,
                        data_encipherment=False,
                        key_agreement=False,
                        encipher_only=False,
                        decipher_only=False,
                    ),
                    critical=True,
                )
            elif certificate_type == CertificateType.CLIENT:
                cert_builder = cert_builder.add_extension(
                    x509.KeyUsage(
                        digital_signature=True,
                        key_encipherment=True,
                        key_cert_sign=True,
                        crl_sign=False,
                        content_commitment=False,
                        data_encipherment=False,
                        key_agreement=False,
                        encipher_only=False,
                        decipher_only=False,
                    ),
                    critical=True,
                )

            # Add basic constraints
            cert_builder = cert_builder.add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            )

            # Sign certificate
            cert = cert_builder.sign(self._ca_private_key, hashes.SHA256())

            # Calculate fingerprints
            sha256_fingerprint = cert.fingerprint(hashes.SHA256()).hex()
            sha1_fingerprint = cert.fingerprint(hashes.SHA1()).hex()

            # Save certificate to database
            certificate = Certificate(
                serial_number=serial_number,
                type=certificate_type.value,
                name=name,
                certificate_pem=cert.public_bytes(serialization.Encoding.PEM).decode(),
                private_key_pem=self.security.encrypt_sensitive_data(
                    private_key.private_bytes(
                        encoding=serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption()
                    ).decode()
                ),
                public_key_pem=private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode(),
                subject_cn=subject_cn,
                subject_o=subject_o,
                subject_ou=subject_ou,
                subject_c=subject_c,
                subject_st=subject_st,
                subject_l=subject_l,
                subject_email=subject_email,
                issuer_cn=self._ca_certificate.subject.get_attributes_for_oid(NameOID.COMMON_NAME)[0].value,
                issuer_o=self._ca_certificate.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME)[0].value if self._ca_certificate.subject.get_attributes_for_oid(NameOID.ORGANIZATION_NAME) else None,
                issuer_c=self._ca_certificate.subject.get_attributes_for_oid(NameOID.COUNTRY_NAME)[0].value if self._ca_certificate.subject.get_attributes_for_oid(NameOID.COUNTRY_NAME) else None,
                not_before=cert.not_valid_before,
                not_after=cert.not_valid_after,
                is_active=True,
                sha256_fingerprint=sha256_fingerprint,
                sha1_fingerprint=sha1_fingerprint,
                algorithm=algorithm,
                key_size=key_size,
                signature_algorithm=cert.signature_hash_algorithm.name,
                san_dns_names=json.dumps(san_dns_names) if san_dns_names else None,
                san_ip_addresses=json.dumps(san_ip_addresses) if san_ip_addresses else None,
                san_emails=json.dumps(san_emails) if san_emails else None,
                auto_renew=auto_renew,
                renewal_threshold_days=self.config.cert_renewal_threshold_days,
            )

            self.db.add(certificate)
            self.db.commit()

            # Log certificate creation
            self.security.log_security_event(
                'CERT_CREATED',
                details={
                    'name': name,
                    'subject_cn': subject_cn,
                    'algorithm': algorithm,
                    'key_size': key_size,
                    'validity_days': validity_days
                }
            )

            return {
                'id': certificate.id,
                'serial_number': serial_number,
                'certificate_pem': cert.public_bytes(serialization.Encoding.PEM).decode(),
                'private_key_pem': private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ).decode(),
                'public_key_pem': private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode(),
                'sha256_fingerprint': sha256_fingerprint,
                'not_before': cert.not_valid_before.isoformat(),
                'not_after': cert.not_valid_after.isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate certificate: {e}")
            raise

    def get_certificate(self, certificate_id: int) -> Optional[Certificate]:
        """
        Get certificate by ID

        Args:
            certificate_id: Certificate ID

        Returns:
            Certificate object or None
        """
        return self.db.query(Certificate).filter_by(id=certificate_id).first()

    def get_certificate_by_serial(self, serial_number: str) -> Optional[Certificate]:
        """
        Get certificate by serial number

        Args:
            serial_number: Certificate serial number

        Returns:
            Certificate object or None
        """
        return self.db.query(Certificate).filter_by(serial_number=serial_number).first()

    def list_certificates(
        self,
        certificate_type: Optional[CertificateType] = None,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List certificates

        Args:
            certificate_type: Filter by type
            active_only: Only active certificates

        Returns:
            List of certificate dictionaries
        """
        try:
            query = self.db.query(Certificate)

            if certificate_type:
                query = query.filter(Certificate.type == certificate_type.value)
            if active_only:
                query = query.filter(Certificate.is_active == True)

            certificates = query.order_by(desc(Certificate.created_at)).all()

            return [cert.to_dict() for cert in certificates]

        except Exception as e:
            logger.error(f"Failed to list certificates: {e}")
            return []

    def verify_certificate(self, certificate_pem: str) -> Dict[str, Any]:
        """
        Verify certificate

        Args:
            certificate_pem: PEM encoded certificate

        Returns:
            Verification result
        """
        try:
            cert = x509.load_pem_x509_certificate(certificate_pem.encode())

            # Check expiration
            now = datetime.utcnow()
            is_expired = now > cert.not_valid_after
            is_not_yet_valid = now < cert.not_valid_before

            # Verify signature
            try:
                if self._ca_certificate:
                    # Verify against CA
                    self._ca_certificate.public_key().verify(
                        cert.signature,
                        cert.tbs_certificate_bytes,
                        cert.signature_hash_algorithm
                    )
                    is_signed_by_ca = True
                else:
                    is_signed_by_ca = None
            except Exception:
                is_signed_by_ca = False

            # Check revocation (simplified - would need CRL/OCSP in production)
            # For now, assume not revoked
            is_revoked = False

            # Get subject information
            subject = {}
            for attr in cert.subject:
                subject[attr.oid._name] = attr.value

            # Get SANs
            try:
                san_ext = cert.extensions.get_extension_for_oid(ExtensionOID.SUBJECT_ALTERNATIVE_NAME)
                dns_names = [name.value for name in san_ext.value.get_values_for_type(x509.DNSName)]
                ip_addresses = [str(name.value) for name in san_ext.value.get_values_for_type(x509.IPAddress)]
                emails = [name.value for name in san_ext.value.get_values_for_type(x509.RFC822Name)]
            except x509.ExtensionNotFound:
                dns_names = []
                ip_addresses = []
                emails = []

            return {
                'valid': not is_expired and not is_not_yet_valid and is_signed_by_ca and not is_revoked,
                'is_expired': is_expired,
                'is_not_yet_valid': is_not_yet_valid,
                'is_signed_by_ca': is_signed_by_ca,
                'is_revoked': is_revoked,
                'subject': subject,
                'dns_names': dns_names,
                'ip_addresses': ip_addresses,
                'emails': emails,
                'not_before': cert.not_valid_before.isoformat(),
                'not_after': cert.not_valid_after.isoformat(),
                'days_until_expiry': (cert.not_valid_after - now).days,
            }

        except Exception as e:
            logger.error(f"Failed to verify certificate: {e}")
            return {
                'valid': False,
                'error': str(e)
            }

    def revoke_certificate(self, certificate_id: int, reason: str = "Unspecified") -> bool:
        """
        Revoke certificate

        Args:
            certificate_id: Certificate ID
            reason: Revocation reason

        Returns:
            True if successful
        """
        try:
            certificate = self.get_certificate(certificate_id)
            if not certificate:
                return False

            certificate.is_revoked = True
            certificate.is_active = False
            certificate.revocation_reason = reason
            certificate.revocation_date = datetime.utcnow()
            self.db.commit()

            self.security.log_security_event(
                'CERT_REVOKED',
                details={
                    'certificate_id': certificate_id,
                    'serial_number': certificate.serial_number,
                    'reason': reason
                }
            )

            return True

        except Exception as e:
            logger.error(f"Failed to revoke certificate: {e}")
            return False

    def renew_certificate(self, certificate_id: int) -> Optional[Dict[str, Any]]:
        """
        Renew certificate

        Args:
            certificate_id: Certificate ID

        Returns:
            New certificate information or None
        """
        try:
            old_cert = self.get_certificate(certificate_id)
            if not old_cert:
                return None

            # Generate new certificate with same subject
            new_cert = self.generate_certificate(
                name=f"{old_cert.name} (Renewed)",
                subject_cn=old_cert.subject_cn,
                subject_o=old_cert.subject_o,
                subject_ou=old_cert.subject_ou,
                subject_c=old_cert.subject_c,
                subject_st=old_cert.subject_st,
                subject_l=old_cert.subject_l,
                subject_email=old_cert.subject_email,
                san_dns_names=json.loads(old_cert.san_dns_names) if old_cert.san_dns_names else None,
                san_ip_addresses=json.loads(old_cert.san_ip_addresses) if old_cert.san_ip_addresses else None,
                san_emails=json.loads(old_cert.san_emails) if old_cert.san_emails else None,
                algorithm=old_cert.algorithm,
                key_size=old_cert.key_size,
                certificate_type=CertificateType(old_cert.type),
                auto_renew=old_cert.auto_renew
            )

            # Revoke old certificate
            self.revoke_certificate(certificate_id, "Renewed")

            self.security.log_security_event(
                'CERT_RENEWED',
                details={
                    'old_certificate_id': certificate_id,
                    'new_certificate_id': new_cert['id']
                }
            )

            return new_cert

        except Exception as e:
            logger.error(f"Failed to renew certificate: {e}")
            return None

    def get_expiring_certificates(self, days: int = 30) -> List[Certificate]:
        """
        Get certificates expiring within specified days

        Args:
            days: Number of days to check

        Returns:
            List of expiring certificates
        """
        try:
            threshold = datetime.utcnow() + timedelta(days=days)
            certificates = self.db.query(Certificate).filter(
                and_(
                    Certificate.not_after <= threshold,
                    Certificate.not_after > datetime.utcnow(),
                    Certificate.is_active == True,
                    Certificate.is_revoked == False
                )
            ).all()

            return certificates

        except Exception as e:
            logger.error(f"Failed to get expiring certificates: {e}")
            return []

    def cleanup_expired_certificates(self) -> int:
        """
        Clean up expired certificates

        Returns:
            Number of certificates cleaned up
        """
        try:
            expired = self.db.query(Certificate).filter(
                and_(
                    Certificate.not_after < datetime.utcnow(),
                    Certificate.is_active == True
                )
            ).all()

            count = 0
            for cert in expired:
                cert.is_active = False
                self.security.log_security_event(
                    'CERT_EXPIRED',
                    details={
                        'certificate_id': cert.id,
                        'serial_number': cert.serial_number
                    }
                )
                count += 1

            self.db.commit()
            return count

        except Exception as e:
            logger.error(f"Failed to cleanup expired certificates: {e}")
            return 0

    def create_csr(
        self,
        name: str,
        subject_cn: str,
        subject_o: Optional[str] = None,
        subject_ou: Optional[str] = None,
        subject_c: Optional[str] = None,
        subject_st: Optional[str] = None,
        subject_l: Optional[str] = None,
        subject_email: Optional[str] = None,
        san_dns_names: Optional[List[str]] = None,
        san_ip_addresses: Optional[List[str]] = None,
        san_emails: Optional[List[str]] = None,
        algorithm: str = 'RSA',
        key_size: int = 2048,
    ) -> Dict[str, str]:
        """
        Create certificate signing request (CSR)

        Args:
            name: CSR name
            subject_cn: Common Name
            subject_o: Organization
            subject_ou: Organizational Unit
            subject_c: Country
            subject_st: State/Province
            subject_l: Locality
            subject_email: Email
            san_dns_names: DNS SANs
            san_ip_addresses: IP SANs
            san_emails: Email SANs
            algorithm: Key algorithm
            key_size: Key size

        Returns:
            Dictionary with CSR and private key
        """
        try:
            # Generate private key
            if algorithm.upper() == 'RSA':
                private_key = rsa.generate_private_key(
                    public_exponent=65537,
                    key_size=key_size,
                )
            else:
                private_key = ec.generate_private_key(ec.SECP256R1())
                key_size = 256

            # Create subject
            subject_attributes = [
                x509.NameAttribute(NameOID.COMMON_NAME, subject_cn),
            ]

            if subject_o:
                subject_attributes.append(x509.NameAttribute(NameOID.ORGANIZATION_NAME, subject_o))
            if subject_ou:
                subject_attributes.append(x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, subject_ou))
            if subject_c:
                subject_attributes.append(x509.NameAttribute(NameOID.COUNTRY_NAME, subject_c))
            if subject_st:
                subject_attributes.append(x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, subject_st))
            if subject_l:
                subject_attributes.append(x509.NameAttribute(NameOID.LOCALITY_NAME, subject_l))
            if subject_email:
                subject_attributes.append(x509.NameAttribute(NameOID.EMAIL_ADDRESS, subject_email))

            subject = x509.Name(subject_attributes)

            # Build CSR
            csr = x509.CertificateSigningRequestBuilder().subject_name(
                subject
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(name) for name in (san_dns_names or [])
                ] + [
                    x509.RFC822Name(email) for email in (san_emails or [])
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())

            # Save CSR to database
            request_id = secrets.token_hex(16)
            csr_record = CertificateRequest(
                request_id=request_id,
                type='server',
                csr_pem=csr.public_bytes(serialization.Encoding.PEM).decode(),
                public_key_pem=private_key.public_key().public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ).decode(),
                subject_cn=subject_cn,
                subject_o=subject_o,
                subject_ou=subject_ou,
                subject_c=subject_c,
                subject_st=subject_st,
                subject_l=subject_l,
                subject_email=subject_email,
                san_dns_names=json.dumps(san_dns_names) if san_dns_names else None,
                san_ip_addresses=json.dumps(san_ip_addresses) if san_ip_addresses else None,
                san_emails=json.dumps(san_emails) if san_emails else None,
                algorithm=algorithm,
                key_size=key_size,
            )

            self.db.add(csr_record)
            self.db.commit()

            return {
                'request_id': request_id,
                'csr_pem': csr.public_bytes(serialization.Encoding.PEM).decode(),
                'private_key_pem': private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ).decode(),
            }

        except Exception as e:
            logger.error(f"Failed to create CSR: {e}")
            raise

    def sign_csr(self, request_id: str) -> Optional[Dict[str, str]]:
        """
        Sign certificate signing request

        Args:
            request_id: CSR request ID

        Returns:
            Certificate information or None
        """
        try:
            csr_record = self.db.query(CertificateRequest).filter_by(
                request_id=request_id,
                status='pending'
            ).first()

            if not csr_record:
                return None

            # In production, would need approval workflow
            # For now, auto-approve

            # Load CSR
            csr = x509.load_pem_x509_csr(csr_record.csr_pem.encode())

            # Generate certificate
            cert_info = self.generate_certificate(
                name=f"CSR: {csr_record.subject_cn}",
                subject_cn=csr_record.subject_cn,
                subject_o=csr_record.subject_o,
                subject_ou=csr_record.subject_ou,
                subject_c=csr_record.subject_c,
                subject_st=csr_record.subject_st,
                subject_l=csr_record.subject_l,
                subject_email=csr_record.subject_email,
                san_dns_names=json.loads(csr_record.san_dns_names) if csr_record.san_dns_names else None,
                san_ip_addresses=json.loads(csr_record.san_ip_addresses) if csr_record.san_ip_addresses else None,
                san_emails=json.loads(csr_record.san_emails) if csr_record.san_emails else None,
                algorithm=csr_record.algorithm,
                key_size=csr_record.key_size,
            )

            # Update CSR record
            csr_record.status = 'signed'
            csr_record.certificate_id = cert_info['id']
            self.db.commit()

            return cert_info

        except Exception as e:
            logger.error(f"Failed to sign CSR: {e}")
            return None
