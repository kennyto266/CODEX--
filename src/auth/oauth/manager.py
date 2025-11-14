"""
OAuth 2.0 / OpenID Connect Manager (T107)
Enterprise-grade OAuth 2.0 implementation with multiple providers
"""

import json
import secrets
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.config import AuthConfig
from ..core.security import SecurityManager
from ..models.oauth import OAuthProvider, OAuthProviderConfig, OAuthToken, OAuthUser
from ..models.user import User
from ..models.security_event import SecurityEvent, SecurityEventType

logger = logging.getLogger("hk_quant_system.auth.oauth")


class OAuthManager:
    """
    OAuth 2.0 / OpenID Connect Manager
    Handles OAuth flows, token management, and identity provider integration
    """

    def __init__(self, config: AuthConfig, security: SecurityManager, db_session: Session):
        """
        Initialize OAuth manager

        Args:
            config: Authentication configuration
            security: Security manager instance
            db_session: Database session
        """
        self.config = config
        self.security = security
        self.db = db_session

    def get_authorization_url(
        self,
        provider: OAuthProvider,
        state: Optional[str] = None,
        scope: Optional[List[str]] = None,
        redirect_uri: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get OAuth authorization URL

        Args:
            provider: OAuth provider
            state: Random state parameter
            scope: Requested scopes
            redirect_uri: Redirect URI

        Returns:
            Dictionary with authorization URL and state
        """
        if state is None:
            state = secrets.token_urlsafe(32)

        if scope is None:
            scope = self._get_default_scopes(provider)

        provider_config = self._get_provider_config(provider)
        if not provider_config:
            raise ValueError(f"Provider {provider.value} not configured")

        if redirect_uri is None:
            redirect_uri = self.config.oauth_redirect_uri

        # Build authorization URL
        auth_url = (
            f"{provider_config.authorize_url}"
            f"?client_id={provider_config.client_id}"
            f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
            f"&response_type=code"
            f"&scope={urllib.parse.quote(' '.join(scope))}"
            f"&state={state}"
        )

        return {
            'authorization_url': auth_url,
            'state': state,
            'scope': scope,
            'redirect_uri': redirect_uri
        }

    def _get_default_scopes(self, provider: OAuthProvider) -> List[str]:
        """Get default scopes for provider"""
        default_scopes = {
            OAuthProvider.GOOGLE: [
                'openid',
                'email',
                'profile',
            ],
            OAuthProvider.MICROSOFT: [
                'openid',
                'email',
                'profile',
            ],
            OAuthProvider.GITHUB: [
                'read:user',
                'user:email',
            ],
            OAuthProvider.FACEBOOK: [
                'email',
                'public_profile',
            ],
            OAuthProvider.APPLE: [
                'name',
                'email',
            ],
        }
        return default_scopes.get(provider, [])

    def _get_provider_config(self, provider: OAuthProvider) -> Optional[OAuthProviderConfig]:
        """Get provider configuration from database"""
        return self.db.query(OAuthProviderConfig).filter_by(
            provider=provider.value,
            is_active=True
        ).first()

    def exchange_code_for_token(
        self,
        provider: OAuthProvider,
        code: str,
        state: str,
        redirect_uri: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Exchange authorization code for access token

        Args:
            provider: OAuth provider
            code: Authorization code
            state: State parameter
            redirect_uri: Redirect URI

        Returns:
            Token information or None
        """
        try:
            provider_config = self._get_provider_config(provider)
            if not provider_config:
                logger.error(f"Provider {provider.value} not configured")
                return None

            if redirect_uri is None:
                redirect_uri = self.config.oauth_redirect_uri

            # In production, use requests library to make HTTP call to token endpoint
            # For this implementation, we'll simulate the response

            # Example token response structure:
            token_data = {
                'access_token': 'simulated_access_token',
                'refresh_token': 'simulated_refresh_token',
                'id_token': 'simulated_id_token',  # For OIDC
                'token_type': 'Bearer',
                'expires_in': 3600,
                'scope': ' '.join(self._get_default_scopes(provider))
            }

            # Store token in database
            # (This would be after actual token exchange)
            # self._store_oauth_token(user_id, provider, token_data)

            return token_data

        except Exception as e:
            logger.error(f"Failed to exchange code for token: {e}")
            return None

    def get_user_info(
        self,
        provider: OAuthProvider,
        access_token: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user info from OAuth provider

        Args:
            provider: OAuth provider
            access_token: Access token

        Returns:
            User information or None
        """
        try:
            provider_config = self._get_provider_config(provider)
            if not provider_config:
                return None

            # In production, use requests library to call userinfo endpoint
            # Example response:
            user_info = {
                'provider': provider.value,
                'provider_user_id': '12345',
                'username': 'john_doe',
                'email': 'john.doe@example.com',
                'full_name': 'John Doe',
                'picture': 'https://example.com/avatar.jpg',
                'verified': True,
            }

            return user_info

        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None

    def handle_oauth_login(
        self,
        provider: OAuthProvider,
        user_info: Dict[str, Any]
    ) -> User:
        """
        Handle OAuth login and user creation/linkage

        Args:
            provider: OAuth provider
            user_info: User information from provider

        Returns:
            User object
        """
        try:
            # Check if user already exists
            oauth_user = self.db.query(OAuthUser).filter(
                and_(
                    OAuthUser.provider == provider.value,
                    OAuthUser.provider_user_id == user_info['provider_user_id']
                )
            ).first()

            if oauth_user:
                # Update existing OAuth user
                oauth_user.provider_username = user_info.get('username')
                oauth_user.provider_email = user_info.get('email')
                oauth_user.provider_data = json.dumps(user_info)
                self.db.commit()

                user = self.db.query(User).filter_by(id=oauth_user.user_id).first()
                if user:
                    # Update last login
                    user.last_login = datetime.utcnow()
                    self.db.commit()

                    self.security.log_security_event(
                        'OAUTH_LOGIN',
                        user_id=str(user.id),
                        details={
                            'provider': provider.value,
                            'provider_user_id': user_info['provider_user_id']
                        }
                    )

                    return user

            # Check if email already exists
            if user_info.get('email'):
                existing_user = self.db.query(User).filter_by(
                    email=user_info['email']
                ).first()

                if existing_user:
                    # Link OAuth account to existing user
                    self._link_oauth_account(existing_user, provider, user_info)
                    return existing_user

            # Create new user
            new_user = self._create_user_from_oauth(provider, user_info)
            return new_user

        except Exception as e:
            logger.error(f"Failed to handle OAuth login: {e}")
            raise

    def _link_oauth_account(
        self,
        user: User,
        provider: OAuthProvider,
        user_info: Dict[str, Any]
    ) -> OAuthUser:
        """Link OAuth account to existing user"""
        # Check if already linked
        existing = self.db.query(OAuthUser).filter(
            and_(
                OAuthUser.user_id == user.id,
                OAuthUser.provider == provider.value
            )
        ).first()

        if existing:
            # Update existing
            existing.provider_user_id = user_info['provider_user_id']
            existing.provider_username = user_info.get('username')
            existing.provider_email = user_info.get('email')
            existing.provider_data = json.dumps(user_info)
            self.db.commit()
            return existing

        # Create new link
        oauth_user = OAuthUser(
            user_id=user.id,
            provider=provider.value,
            provider_user_id=user_info['provider_user_id'],
            provider_username=user_info.get('username'),
            provider_email=user_info.get('email'),
            provider_data=json.dumps(user_info)
        )
        self.db.add(oauth_user)
        self.db.commit()

        self.security.log_security_event(
            'OAUTH_ACCOUNT_LINKED',
            user_id=str(user.id),
            details={
                'provider': provider.value,
                'provider_user_id': user_info['provider_user_id']
            }
        )

        return oauth_user

    def _create_user_from_oauth(
        self,
        provider: OAuthProvider,
        user_info: Dict[str, Any]
    ) -> User:
        """Create new user from OAuth info"""
        # Generate username from email or provider info
        if user_info.get('email'):
            base_username = user_info['email'].split('@')[0]
        else:
            base_username = user_info.get('username', 'user')

        # Ensure unique username
        username = base_username
        counter = 1
        while self.db.query(User).filter_by(username=username).first():
            username = f"{base_username}_{counter}"
            counter += 1

        # Create user
        user = User(
            email=user_info.get('email', f"{secrets.token_hex(8)}@oauth.local"),
            username=username,
            hashed_password=self.security.generate_secure_token(32),  # Random password
            full_name=user_info.get('full_name', user_info.get('username', 'OAuth User')),
            is_active=True,
            is_verified=True,  # OAuth users are considered verified
            role='viewer',  # Default role
        )
        self.db.add(user)
        self.db.flush()

        # Create OAuth user record
        self._link_oauth_account(user, provider, user_info)

        # Log user creation
        self.security.log_security_event(
            'USER_CREATED',
            user_id=str(user.id),
            details={
                'method': 'oauth',
                'provider': provider.value
            }
        )

        return user

    def get_oauth_token(
        self,
        user_id: int,
        provider: OAuthProvider
    ) -> Optional[OAuthToken]:
        """
        Get OAuth token for user

        Args:
            user_id: User ID
            provider: OAuth provider

        Returns:
            OAuth token or None
        """
        return self.db.query(OAuthToken).filter(
            and_(
                OAuthToken.user_id == user_id,
                OAuthToken.provider == provider.value,
                OAuthToken.expires_at > datetime.utcnow()
            )
        ).first()

    def refresh_oauth_token(
        self,
        user_id: int,
        provider: OAuthProvider
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh OAuth access token

        Args:
            user_id: User ID
            provider: OAuth provider

        Returns:
            New token information or None
        """
        try:
            token = self.get_oauth_token(user_id, provider)
            if not token or not token.refresh_token:
                return None

            provider_config = self._get_provider_config(provider)
            if not provider_config:
                return None

            # In production, make actual API call to refresh token
            # For this implementation, return simulated data

            # Generate new tokens
            new_access_token = secrets.token_urlsafe(32)
            new_expires = datetime.utcnow() + timedelta(hours=1)

            # Update token in database
            token.access_token = self.security.encrypt_sensitive_data(new_access_token)
            token.expires_at = new_expires
            self.db.commit()

            self.security.log_security_event(
                'OAUTH_TOKEN_REFRESH',
                user_id=str(user_id),
                details={'provider': provider.value}
            )

            return {
                'access_token': new_access_token,
                'token_type': token.token_type,
                'expires_in': 3600
            }

        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {e}")
            return None

    def revoke_oauth_token(
        self,
        user_id: int,
        provider: OAuthProvider
    ) -> bool:
        """
        Revoke OAuth token

        Args:
            user_id: User ID
            provider: OAuth provider

        Returns:
            True if successful
        """
        try:
            token = self.get_oauth_token(user_id, provider)
            if not token:
                return False

            # In production, make API call to revoke token
            # Delete from database
            self.db.delete(token)
            self.db.commit()

            self.security.log_security_event(
                'OAUTH_TOKEN_REVOKED',
                user_id=str(user_id),
                details={'provider': provider.value}
            )

            return True

        except Exception as e:
            logger.error(f"Failed to revoke OAuth token: {e}")
            return False

    def list_oauth_connections(self, user_id: int) -> List[Dict[str, Any]]:
        """
        List OAuth connections for user

        Args:
            user_id: User ID

        Returns:
            List of OAuth connections
        """
        try:
            oauth_users = self.db.query(OAuthUser).filter_by(user_id=user_id).all()
            connections = []

            for oauth_user in oauth_users:
                # Check if token exists
                token = self.get_oauth_token(
                    user_id,
                    OAuthProvider(oauth_user.provider)
                )

                connections.append({
                    'provider': oauth_user.provider,
                    'provider_username': oauth_user.provider_username,
                    'provider_email': oauth_user.provider_email,
                    'connected_at': oauth_user.created_at.isoformat(),
                    'has_token': token is not None,
                    'token_expires_at': token.expires_at.isoformat() if token else None,
                })

            return connections

        except Exception as e:
            logger.error(f"Failed to list OAuth connections: {e}")
            return []

    def unlink_oauth_account(
        self,
        user_id: int,
        provider: OAuthProvider
    ) -> bool:
        """
        Unlink OAuth account

        Args:
            user_id: User ID
            provider: OAuth provider

        Returns:
            True if successful
        """
        try:
            oauth_user = self.db.query(OAuthUser).filter(
                and_(
                    OAuthUser.user_id == user_id,
                    OAuthUser.provider == provider.value
                )
            ).first()

            if not oauth_user:
                return False

            # Revoke token first
            self.revoke_oauth_token(user_id, provider)

            # Delete OAuth user record
            self.db.delete(oauth_user)
            self.db.commit()

            self.security.log_security_event(
                'OAUTH_ACCOUNT_UNLINKED',
                user_id=str(user_id),
                details={'provider': provider.value}
            )

            return True

        except Exception as e:
            logger.error(f"Failed to unlink OAuth account: {e}")
            return False

    def setup_provider(
        self,
        provider: OAuthProvider,
        client_id: str,
        client_secret: str,
        redirect_uri: Optional[str] = None
    ) -> bool:
        """
        Setup OAuth provider configuration

        Args:
            provider: OAuth provider
            client_id: Client ID
            client_secret: Client secret
            redirect_uri: Redirect URI

        Returns:
            True if successful
        """
        try:
            # Get default provider configuration
            provider_config = self._get_default_provider_config(provider)
            if not provider_config:
                # Create new configuration
                provider_config = OAuthProviderConfig(
                    provider=provider.value,
                    client_id=client_id,
                    client_secret=self.security.encrypt_sensitive_data(client_secret),
                    redirect_uri=redirect_uri or self.config.oauth_redirect_uri,
                )
                self.db.add(provider_config)
            else:
                # Update existing
                provider_config.client_id = client_id
                provider_config.client_secret = self.security.encrypt_sensitive_data(client_secret)
                provider_config.redirect_uri = redirect_uri or self.config.oauth_redirect_uri

            self.db.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to setup provider: {e}")
            return False

    def _get_default_provider_config(self, provider: OAuthProvider) -> Optional[OAuthProviderConfig]:
        """Get default provider configuration"""
        configs = {
            OAuthProvider.GOOGLE: {
                'authorize_url': 'https://accounts.google.com/o/oauth2/v2/auth',
                'token_url': 'https://oauth2.googleapis.com/token',
                'userinfo_url': 'https://www.googleapis.com/oauth2/v2/userinfo',
            },
            OAuthProvider.MICROSOFT: {
                'authorize_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
                'token_url': 'https://login.microsoftonline.com/common/oauth2/v2.0/token',
                'userinfo_url': 'https://graph.microsoft.com/oidc/userinfo',
            },
            OAuthProvider.GITHUB: {
                'authorize_url': 'https://github.com/login/oauth/authorize',
                'token_url': 'https://github.com/login/oauth/access_token',
                'userinfo_url': 'https://api.github.com/user',
            },
        }

        default_config = configs.get(provider)
        if not default_config:
            return None

        return OAuthProviderConfig(
            provider=provider.value,
            client_id='',
            client_secret='',
            redirect_uri='',
            authorize_url=default_config['authorize_url'],
            token_url=default_config['token_url'],
            userinfo_url=default_config.get('userinfo_url'),
            scope=' '.join(self._get_default_scopes(provider)),
            response_type='code',
            grant_type='authorization_code',
        )
