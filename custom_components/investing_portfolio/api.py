"""API client for Investing.com."""
from __future__ import annotations

import hashlib
import logging
import secrets
import unicodedata
import json
from typing import Any
from urllib.parse import urlencode, quote

import aiohttp

_LOGGER = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "https://aappapi.investing.com"
DEFAULT_X_META_VER = "14"
DEFAULT_X_APP_VER = "1408"
DEFAULT_INTERNAL_VERSION = "1293"


def generate_x_udid(seed: str | None = None) -> str:
    """Generate a unique device identifier (16 hex characters).
    
    If a seed is provided, generates a deterministic UDID based on the seed.
    Otherwise, generates a random UDID.
    """
    if seed:
        # Create deterministic UDID from seed (e.g., Home Assistant instance ID)
        hash_bytes = hashlib.sha256(seed.encode()).digest()[:8]
        return hash_bytes.hex()
    else:
        # Generate random UDID
        return secrets.token_hex(8)


def normalize_portfolio_name(name: str) -> str:
    """Normalize portfolio name for use in entity IDs.
    
    Converts to lowercase, removes accents, replaces spaces with underscores.
    Example: "John's Crypto" -> "johns_crypto"
    """
    # Normalize unicode characters (NFD decomposes accented chars)
    normalized = unicodedata.normalize('NFD', name)
    # Remove diacritical marks (accents)
    ascii_name = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    # Convert to lowercase and replace spaces with underscores
    result = ascii_name.lower().replace(" ", "_")
    # Remove any other non-alphanumeric characters except underscore
    result = ''.join(c for c in result if c.isalnum() or c == '_')
    return result


class InvestingAPIError(Exception):
    """Base exception for Investing API errors."""
    pass


class AuthenticationError(InvestingAPIError):
    """Authentication failed."""
    pass


class PortfolioError(InvestingAPIError):
    """Error fetching portfolios."""
    pass


class TokenExpiredError(AuthenticationError):
    """The authentication token has expired or is invalid."""
    pass


class PortfolioNotFoundError(PortfolioError):
    """The requested portfolio was not found."""
    pass


class InvestingAPI:
    """Client for Investing.com API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client.
        
        Args:
            session: An aiohttp ClientSession (use async_get_clientsession from HA).
        """
        self._session = session


    async def login(
        self, 
        email: str, 
        password: str, 
        x_udid: str
    ) -> dict[str, Any]:
        """Perform login and return user data with token.
        
        Args:
            email: User email
            password: User password (plain text, will be MD5 hashed)
            x_udid: Device unique identifier
            
        Returns:
            dict with 'token', 'user_id', 'user_email', etc.
            
        Raises:
            AuthenticationError: If login fails
        """
        # Hash password with MD5
        password_hash = hashlib.md5(password.encode()).hexdigest()
        
        # Build query parameters
        query_data = {"action": "login"}
        query_params = {
            "time_utc_offset": "3600",
            "skinID": "2",
            "lang_ID": "4",
            "data": json.dumps(query_data, separators=(',', ':')),
        }
        
        url = f"{API_BASE_URL}/login_api.php?{urlencode(query_params)}"
        
        headers = {
            "x-udid": x_udid,
            "x-app-ver": DEFAULT_X_APP_VER,
            "x-meta-ver": DEFAULT_X_META_VER,
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 3 Build/QQ1D.200105.002)",
        }
        
        body = urlencode({
            "internal_version": DEFAULT_INTERNAL_VERSION,
            "reg_initiator": "Side Menu Sign In",
            "email": email,
            "smssupport": "1",
            "password": password_hash,
            "reg_source": "android",
        })
        
        _LOGGER.debug("Attempting login for %s", email)
        
        async with self._session.post(url, headers=headers, data=body, timeout=30) as response:
            if response.status != 200:
                raise AuthenticationError(f"HTTP error {response.status}")
            
            result = await response.json()
            
        # Check for errors in response
        system = result.get("system", {})
        if system.get("status") == "error":
            messages = system.get("messages", {})
            error_msg = messages.get("display_message", "Unknown error")
            _LOGGER.error("Login failed: %s", error_msg)
            raise AuthenticationError(error_msg)
        
        # Extract user data
        data = result.get("data", {})
        if "errors" in data:
            error = data["errors"][0] if data["errors"] else {}
            raise AuthenticationError(error.get("fieldError", "Login failed"))
        
        if "token" not in data:
            raise AuthenticationError("No token in response")
        
        _LOGGER.info("Login successful for user %s", data.get("user_email"))
        
        return {
            "token": data["token"],
            "user_id": data.get("user_ID"),
            "user_email": data.get("user_email"),
            "user_firstname": data.get("user_firstname"),
            "user_lastname": data.get("user_lastname"),
        }

    async def get_portfolios(
        self, 
        x_token: str, 
        x_udid: str,
        position_only: bool = True
    ) -> list[dict[str, Any]]:
        """Get all portfolios for the authenticated user."""
        query_data = [{
            "action": "get_all_portfolios_new",
            "bring_sums": False,
            "include_pair_attr": False,
            "include_pairs": True,
        }]
        
        query_params = {
            "time_utc_offset": "3600",
            "skinID": "2",
            "lang_ID": "4",
            "data": json.dumps(query_data, separators=(',', ':')),
        }
        
        url = f"{API_BASE_URL}/portfolio_api.php?{urlencode(query_params)}"
        
        headers = {
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 3 Build/QQ1D.200105.002)",
            "Accept": "application/json",
            "x-token": x_token,
            "x-udid": x_udid,
            "x-app-ver": DEFAULT_X_APP_VER,
            "x-meta-ver": DEFAULT_X_META_VER,
            "Accept-Encoding": "gzip",
        }
        
        _LOGGER.debug("Fetching portfolios")
        
        async with self._session.get(url, headers=headers, timeout=30) as response:
            if response.status != 200:
                raise PortfolioError(f"HTTP error {response.status}")
            
            result = await response.json()
        
        # Check for errors
        system = result.get("system", {})
        if system.get("status") == "failed":
            error_code = system.get("message_error_code", "unknown")
            if error_code == "1001":
                raise TokenExpiredError("Token expired or invalid")
            raise PortfolioError(f"API error: {error_code}")
        
        # Extract portfolios
        try:
            data = result.get("data", [])
            if not data:
                return []
            
            screen_data = data[0].get("screen_data", {})
            portfolios = screen_data.get("portfolio", [])
            
            if position_only:
                portfolios = [
                    p for p in portfolios 
                    if p.get("portfolioType") == "position"
                ]
            
            return portfolios
            
        except (KeyError, IndexError) as err:
            raise PortfolioError(f"Error parsing response: {err}") from err

    async def get_portfolio_summary(
        self,
        portfolio_id: int,
        x_token: str,
        x_udid: str
    ) -> dict[str, Any]:
        """Fetch summary data for a specific portfolio.
        
        Includes MarketValue, OpenPL, DailyPL, etc.
        """
        query_data = {
            "action": "get_portfolio_positions",
            "bring_sums": False,
            "include_pair_attr": False,
            "pair_id": 0,
            "portfolioid": portfolio_id,
            "positionType": "summary"
        }
        
        query_params = {
            "data": json.dumps(query_data, separators=(',', ':')),
            "lang_ID": "4",
            "time_utc_offset": "3600",
            "skinID": "2"
        }
        
        url = f"{API_BASE_URL}/portfolio_api.php?{urlencode(query_params)}"
        
        headers = {
            "x-udid": x_udid,
            "x-token": x_token,
            "x-app-ver": DEFAULT_X_APP_VER,
            "x-meta-ver": DEFAULT_X_META_VER,
            "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 10; Pixel 3 Build/QQ1D.200105.002)",
        }
        
        _LOGGER.debug("Fetching summary for portfolio %s", portfolio_id)
        
        async with self._session.get(url, headers=headers, timeout=30) as response:
            if response.status != 200:
                raise PortfolioError(f"HTTP error {response.status}")
            
            result = await response.json()
            
        # Check for system errors
        system = result.get("system", {})
        if system.get("status") == "failed":
            error_code = system.get("message_error_code", "unknown")
            if error_code == "1001":
                raise TokenExpiredError("Token expired or invalid")
            if error_code == "203":
                raise PortfolioNotFoundError(f"Portfolio {portfolio_id} not found")
            raise PortfolioError(f"API error: {error_code}")
            
        # Parse logic
        try:
            data_list = result.get("data", [])
            if not data_list:
                raise PortfolioError("No data in response")
            
            summary = data_list[0].get("screen_data", {})
            if not summary:
                raise PortfolioError("Missing expected screen_data")
                
            return {
                "market_value": summary.get("MarketValue", "0"),
                "open_pl": summary.get("OpenPL", "0"),
                "open_pl_perc": summary.get("OpenPLPerc", "0"),
                "daily_pl": summary.get("DailyPL", "0"),
                "daily_pl_perc": summary.get("DailyPLPerc", "0"),
                "raw_data": summary
            }
            
        except (KeyError, IndexError) as err:
            raise PortfolioError(f"Error parsing summary response: {err}") from err
