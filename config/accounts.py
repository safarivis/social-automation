"""
Multi-Account Configuration for Social Platforms

Supports multiple accounts per platform with easy switching.
"""
import os
from typing import Dict, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_path = Path.home() / "Agents" / ".env"
load_dotenv(env_path)


class AccountManager:
    """Manages multiple accounts across platforms"""

    def __init__(self):
        self._accounts: Dict[str, Dict[str, Dict[str, Any]]] = {
            "twitter": {},
            "linkedin": {},
            "tiktok": {},
            "instagram": {},
            "youtube": {},
        }
        self._active_accounts: Dict[str, str] = {}
        self._load_accounts()

    def _load_accounts(self):
        """Load all accounts from environment variables"""

        # Twitter accounts
        # Personal account (default)
        if os.getenv("TWITTER_ACCESS_TOKEN"):
            self._accounts["twitter"]["personal"] = {
                "name": "Personal",
                "api_key": os.getenv("TWITTER_API_KEY"),
                "api_secret": os.getenv("TWITTER_API_SECRET"),
                "access_token": os.getenv("TWITTER_ACCESS_TOKEN"),
                "access_secret": os.getenv("TWITTER_ACCESS_SECRET"),
                "bearer_token": os.getenv("TWITTER_BEARER_TOKEN"),
            }
            self._active_accounts["twitter"] = "personal"

        # Lewkai company account (OAuth 2.0)
        if os.getenv("TWITTER_LEWKAI_ACCESS_TOKEN"):
            self._accounts["twitter"]["lewkai"] = {
                "name": "Lewkai (@lewkai_)",
                "auth_type": "oauth2",  # Uses OAuth 2.0 instead of 1.0a
                "client_id": os.getenv("TWITTER_CLIENT_ID"),
                "client_secret": os.getenv("TWITTER_CLIENT_SECRET"),
                "access_token": os.getenv("TWITTER_LEWKAI_ACCESS_TOKEN"),
                "refresh_token": os.getenv("TWITTER_LEWKAI_REFRESH_TOKEN"),
            }

        # LinkedIn accounts
        # Personal account
        if os.getenv("LINKEDIN_ACCESS_TOKEN"):
            self._accounts["linkedin"]["personal"] = {
                "name": "Personal",
                "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
                "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET"),
                "access_token": os.getenv("LINKEDIN_ACCESS_TOKEN"),
                "person_urn": os.getenv("LINKEDIN_PERSON_URN"),
                "type": "personal",
            }
            self._active_accounts["linkedin"] = "personal"

        # Lewkai company page
        if os.getenv("LINKEDIN_LEWKAI_ACCESS_TOKEN"):
            self._accounts["linkedin"]["lewkai"] = {
                "name": "Lewkai (Company Page)",
                "client_id": os.getenv("LINKEDIN_CLIENT_ID"),
                "client_secret": os.getenv("LINKEDIN_CLIENT_SECRET"),
                "access_token": os.getenv("LINKEDIN_LEWKAI_ACCESS_TOKEN"),
                "organization_urn": os.getenv("LINKEDIN_LEWKAI_ORG_URN", "urn:li:organization:111720392"),
                "type": "organization",
            }

        # TikTok accounts
        if os.getenv("TIKTOK_ACCESS_TOKEN"):
            self._accounts["tiktok"]["personal"] = {
                "name": "Personal",
                "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
                "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
                "access_token": os.getenv("TIKTOK_ACCESS_TOKEN"),
            }
            self._active_accounts["tiktok"] = "personal"

        if os.getenv("TIKTOK_LEWKAI_ACCESS_TOKEN"):
            self._accounts["tiktok"]["lewkai"] = {
                "name": "Lewkai",
                "client_key": os.getenv("TIKTOK_CLIENT_KEY"),
                "client_secret": os.getenv("TIKTOK_CLIENT_SECRET"),
                "access_token": os.getenv("TIKTOK_LEWKAI_ACCESS_TOKEN"),
            }

        # Instagram accounts
        if os.getenv("INSTAGRAM_ACCESS_TOKEN"):
            self._accounts["instagram"]["personal"] = {
                "name": "Personal",
                "access_token": os.getenv("INSTAGRAM_ACCESS_TOKEN"),
                "business_id": os.getenv("INSTAGRAM_BUSINESS_ID"),
            }
            self._active_accounts["instagram"] = "personal"

        if os.getenv("INSTAGRAM_LEWKAI_ACCESS_TOKEN"):
            self._accounts["instagram"]["lewkai"] = {
                "name": "Lewkai",
                "access_token": os.getenv("INSTAGRAM_LEWKAI_ACCESS_TOKEN"),
                "business_id": os.getenv("INSTAGRAM_LEWKAI_BUSINESS_ID"),
            }

        # YouTube accounts
        if os.getenv("YOUTUBE_ACCESS_TOKEN"):
            self._accounts["youtube"]["personal"] = {
                "name": "Personal",
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "access_token": os.getenv("YOUTUBE_ACCESS_TOKEN"),
                "refresh_token": os.getenv("YOUTUBE_REFRESH_TOKEN"),
            }
            self._active_accounts["youtube"] = "personal"

        if os.getenv("YOUTUBE_LEWKAI_ACCESS_TOKEN"):
            self._accounts["youtube"]["lewkai"] = {
                "name": "Lewkai",
                "client_id": os.getenv("GOOGLE_CLIENT_ID"),
                "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
                "access_token": os.getenv("YOUTUBE_LEWKAI_ACCESS_TOKEN"),
                "refresh_token": os.getenv("YOUTUBE_LEWKAI_REFRESH_TOKEN"),
            }

    def get_accounts(self, platform: str) -> Dict[str, Dict[str, Any]]:
        """Get all accounts for a platform"""
        return self._accounts.get(platform.lower(), {})

    def get_account(self, platform: str, account_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific account"""
        return self._accounts.get(platform.lower(), {}).get(account_id)

    def get_active_account(self, platform: str) -> Optional[Dict[str, Any]]:
        """Get the currently active account for a platform"""
        platform = platform.lower()
        account_id = self._active_accounts.get(platform)
        if account_id:
            return self._accounts.get(platform, {}).get(account_id)
        return None

    def get_active_account_id(self, platform: str) -> Optional[str]:
        """Get the ID of the currently active account"""
        return self._active_accounts.get(platform.lower())

    def set_active_account(self, platform: str, account_id: str) -> bool:
        """Set the active account for a platform"""
        platform = platform.lower()
        if account_id in self._accounts.get(platform, {}):
            self._active_accounts[platform] = account_id
            return True
        return False

    def list_accounts(self, platform: str) -> list:
        """List all account IDs for a platform"""
        return list(self._accounts.get(platform.lower(), {}).keys())

    def list_all_accounts(self) -> Dict[str, list]:
        """List all accounts for all platforms"""
        return {
            platform: list(accounts.keys())
            for platform, accounts in self._accounts.items()
            if accounts
        }

    def add_account(self, platform: str, account_id: str, credentials: Dict[str, Any]):
        """Add a new account (runtime only, doesn't persist to .env)"""
        platform = platform.lower()
        if platform not in self._accounts:
            self._accounts[platform] = {}
        self._accounts[platform][account_id] = credentials

        # Set as active if it's the first account
        if platform not in self._active_accounts:
            self._active_accounts[platform] = account_id


# Global instance
account_manager = AccountManager()


def get_account(platform: str, account_id: str = None) -> Optional[Dict[str, Any]]:
    """Get account credentials. If account_id is None, returns active account."""
    if account_id:
        return account_manager.get_account(platform, account_id)
    return account_manager.get_active_account(platform)


def set_active_account(platform: str, account_id: str) -> bool:
    """Set the active account for a platform"""
    return account_manager.set_active_account(platform, account_id)


def list_accounts(platform: str = None) -> Dict[str, list]:
    """List accounts. If platform specified, returns just that platform's accounts."""
    if platform:
        return {platform: account_manager.list_accounts(platform)}
    return account_manager.list_all_accounts()
