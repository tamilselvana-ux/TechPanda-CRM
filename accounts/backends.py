"""
Authentication backends for iTechPanda CRM.
Supports email-based authentication with case-insensitive matching.
Hardened with schema auto-healing and deferred column fallbacks for production resilience.
"""

import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db import OperationalError, connection

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailAuthBackend(ModelBackend):
    """
    Authenticate against settings.AUTH_USER_MODEL using an email address
    (case-insensitive). Also falls back to username if an existing system call
    passes a username.
    Resilient to pending migrations by auto-healing or deferring missing columns.
    """

    def _heal_schema_if_needed(self):
        try:
            with connection.cursor() as cursor:
                if connection.vendor == 'mysql':
                    cursor.execute("ALTER TABLE `accounts_user` ADD COLUMN `is_on_duty` TINYINT(1) NOT NULL DEFAULT 1;")
                elif connection.vendor == 'sqlite':
                    cursor.execute("ALTER TABLE accounts_user ADD COLUMN is_on_duty BOOLEAN DEFAULT 1;")
                logger.info("Successfully added missing is_on_duty column to accounts_user.")
                return True
        except Exception as e:
            logger.warning("Could not auto-alter accounts_user: %s", e)
            return False

    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        login_identifier = email or username or kwargs.get('email') or kwargs.get('username')
        if not login_identifier or not password:
            return None

        login_identifier = str(login_identifier).strip()

        # Primary lookup: email (case-insensitive)
        user = None
        try:
            user = User.objects.filter(email__iexact=login_identifier).first()
        except OperationalError as exc:
            if "is_on_duty" in str(exc):
                if self._heal_schema_if_needed():
                    user = User.objects.filter(email__iexact=login_identifier).first()
                else:
                    user = User.objects.defer('is_on_duty').filter(email__iexact=login_identifier).first()
            else:
                raise

        # Secondary fallback lookup: username (case-insensitive)
        if not user:
            try:
                user = User.objects.filter(username__iexact=login_identifier).first()
            except OperationalError as exc:
                if "is_on_duty" in str(exc):
                    if self._heal_schema_if_needed():
                        user = User.objects.filter(username__iexact=login_identifier).first()
                    else:
                        user = User.objects.defer('is_on_duty').filter(username__iexact=login_identifier).first()
                else:
                    raise

        if user:
            # Ensure in-memory is_on_duty attribute exists if column was deferred
            if not hasattr(user, 'is_on_duty'):
                user.is_on_duty = True

            if user.check_password(password) and self.user_can_authenticate(user):
                return user

        return None

    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            return user
        except User.DoesNotExist:
            return None
        except OperationalError as exc:
            if "is_on_duty" in str(exc):
                if self._heal_schema_if_needed():
                    try:
                        return User.objects.get(pk=user_id)
                    except User.DoesNotExist:
                        return None
                else:
                    try:
                        user = User.objects.defer('is_on_duty').get(pk=user_id)
                        if not hasattr(user, 'is_on_duty'):
                            user.is_on_duty = True
                        return user
                    except User.DoesNotExist:
                        return None
            raise
