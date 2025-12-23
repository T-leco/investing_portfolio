"""Data coordinator for Investing Portfolio integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.persistent_notification import async_create

from .api import normalize_portfolio_name, InvestingAPI, TokenExpiredError, PortfolioNotFoundError, PortfolioError
from .const import (
    DOMAIN,
    API_URL,
    DEFAULT_X_APP_VER,
    CONF_UPDATE_WEEKDAY_INTERVAL,
    CONF_UPDATE_WEEKDAY_START,
    CONF_UPDATE_WEEKDAY_END,
    CONF_UPDATE_NIGHT_TIME,
    CONF_UPDATE_MORNING_TIME,
    DEFAULT_UPDATE_WEEKDAY_INTERVAL,
    DEFAULT_UPDATE_WEEKDAY_START,
    DEFAULT_UPDATE_WEEKDAY_END,
    DEFAULT_UPDATE_NIGHT_TIME,
    DEFAULT_UPDATE_MORNING_TIME,
    ERROR_TOKEN_EXPIRED,
    ERROR_INVALID_PORTFOLIO,
    NOTIFICATION_TITLE,
)

_LOGGER = logging.getLogger(__name__)


def parse_european_number(value: str) -> float:
    """Convert European number format to float.
    
    Examples:
        "240.937,98" -> 240937.98
        "41,71%" -> 41.71
        "+70.864,27" -> 70864.27
        "-1.615,47" -> -1615.47
    """
    if not value:
        return 0.0
    # Remove currency symbols, percentage signs, and spaces
    cleaned = value.replace("%", "").replace("€", "").replace(" ", "").strip()
    # Handle positive/negative signs
    is_negative = cleaned.startswith("-")
    cleaned = cleaned.lstrip("+-")
    # Convert European format: remove dots (thousands), replace comma with dot
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        result = float(cleaned)
        return -result if is_negative else result
    except ValueError:
        _LOGGER.warning("Could not parse number: %s", value)
        return 0.0


def parse_time(time_str: str) -> tuple[int, int]:
    """Parse time string HH:MM to (hour, minute) tuple."""
    parts = time_str.split(":")
    return int(parts[0]), int(parts[1])


class InvestingDataCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to fetch data from Investing.com API."""

    def __init__(
        self,
        hass: HomeAssistant,
        x_token: str,
        x_udid: str,
        portfolio_id: int,
        portfolio_name: str,
        options: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{normalize_portfolio_name(portfolio_name)}",
            update_interval=timedelta(minutes=1),  # Check every minute for cron
        )
        self.x_token = x_token
        self.x_udid = x_udid
        self.portfolio_id = portfolio_id
        self.portfolio_name = portfolio_name
        self.normalized_name = normalize_portfolio_name(portfolio_name)
        self._last_successful_data: dict[str, Any] | None = None
        self._last_update_minute: int = -1
        self._error_notified = False
        
        # Use Home Assistant's shared aiohttp session
        self._session = async_get_clientsession(hass)
        
        # Configurable update schedule
        options = options or {}
        self.update_weekday_interval = options.get(
            CONF_UPDATE_WEEKDAY_INTERVAL, DEFAULT_UPDATE_WEEKDAY_INTERVAL
        )
        self.update_weekday_start = options.get(
            CONF_UPDATE_WEEKDAY_START, DEFAULT_UPDATE_WEEKDAY_START
        )
        self.update_weekday_end = options.get(
            CONF_UPDATE_WEEKDAY_END, DEFAULT_UPDATE_WEEKDAY_END
        )
        self.update_night_time = options.get(
            CONF_UPDATE_NIGHT_TIME, DEFAULT_UPDATE_NIGHT_TIME
        )
        self.update_morning_time = options.get(
            CONF_UPDATE_MORNING_TIME, DEFAULT_UPDATE_MORNING_TIME
        )

    def should_update_now(self) -> tuple[bool, int]:
        """Check if we should update based on the cron schedule.
        
        Returns tuple of (should_update, seconds_until_next_check)
        
        Default schedules (configurable):
        - */15 9-21 * * 1,2,3,4,5 (Every 15 min from 9-21, Mon-Fri)
        - 05 22 * * * (22:05 every day)
        - 00 04 * * * (04:00 every day)
        """
        now = datetime.now()
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour
        minute = now.minute
        
        # Parse configurable times
        morning_hour, morning_minute = parse_time(self.update_morning_time)
        night_hour, night_minute = parse_time(self.update_night_time)
        
        # Check morning update (daily)
        if hour == morning_hour and minute == morning_minute:
            return True, 60
        
        # Check night update (daily)
        if hour == night_hour and minute == night_minute:
            return True, 60
        
        # Check weekday trading hours (Mon-Fri, configurable hours, every N min)
        if weekday < 5:  # Monday to Friday
            if self.update_weekday_start <= hour < self.update_weekday_end:
                # Update on configured interval
                if minute % self.update_weekday_interval == 0:
                    return True, 60
        
        # Calculate next update time
        next_check = 60  # Check every minute by default
        return False, next_check

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from API based on cron schedule."""
        now = datetime.now()
        current_minute = now.hour * 60 + now.minute
        
        # Check if we should update based on cron schedule
        should_update, _ = self.should_update_now()
        
        # Avoid duplicate updates in the same minute
        if current_minute == self._last_update_minute:
            if self._last_successful_data:
                return self._last_successful_data
            raise UpdateFailed("Waiting for scheduled update")
        
        if not should_update:
            # Return cached data if available, otherwise raise
            if self._last_successful_data:
                return self._last_successful_data
            # First run - fetch initial data
            _LOGGER.debug("Initial data fetch for %s", self.portfolio_name)
        
        self._last_update_minute = current_minute
        
        return await self._fetch_data()

    async def _fetch_data(self) -> dict[str, Any]:
        """Fetch data from API using InvestingAPI client."""
        try:
            api = InvestingAPI(self._session)
            summary = await api.get_portfolio_summary(
                self.portfolio_id,
                self.x_token,
                self.x_udid
            )
        except TokenExpiredError as err:
            error_message = (
                f"❌ Authentication token expired or invalid for '{self.portfolio_name}'. "
                "Please delete the integration entry and re-configure it with your credentials. "
                f"Error: {err}"
            )
            if not self._error_notified:
                await self._notify_error(error_message)
                self._error_notified = True
            _LOGGER.error(error_message)
            raise UpdateFailed(error_message) from err
            
        except PortfolioNotFoundError as err:
            error_message = (
                f"❌ Invalid portfolio ID for '{self.portfolio_name}'. "
                f"Error: {err}"
            )
            _LOGGER.error(error_message)
            raise UpdateFailed(error_message) from err
            
        except PortfolioError as err:
            error_message = f"API error for '{self.portfolio_name}': {err}"
            _LOGGER.error(error_message)
            raise UpdateFailed(error_message) from err
            
        except Exception as err:
            error_message = f"Unexpected error fetching data for '{self.portfolio_name}': {err}"
            _LOGGER.error(error_message)
            raise UpdateFailed(error_message) from err

        # Reset error notification flag on success
        self._error_notified = False

        # Parse the response (using helper from coordinator for number formats)
        try:
            parsed_data = {
                "portfolio_name": self.portfolio_name,
                "market_value": parse_european_number(summary.get("market_value", "0")),
                "open_pl": parse_european_number(summary.get("open_pl", "0")),
                "open_pl_perc": parse_european_number(summary.get("open_pl_perc", "0")),
                "daily_pl": parse_european_number(summary.get("daily_pl", "0")),
                "daily_pl_perc": parse_european_number(summary.get("daily_pl_perc", "0")),
                "timestamp": datetime.now().isoformat(),
                "raw_data": summary.get("raw_data"),
            }
            
            self._last_successful_data = parsed_data
            _LOGGER.debug("Data fetched successfully for %s: %s", self.portfolio_name, parsed_data)
            
            return parsed_data
            
        except (KeyError, IndexError) as err:
            error_msg = f"Error parsing API response: {err}"
            _LOGGER.error(error_msg)
            raise UpdateFailed(error_msg) from err

    async def async_force_refresh(self) -> None:
        """Force an immediate data refresh (for manual button)."""
        self._last_update_minute = -1  # Reset to allow update
        await self._fetch_data()
        self.async_set_updated_data(self._last_successful_data)

    async def _notify_error(self, message: str) -> None:
        """Send a persistent notification about the error."""
        async_create(
            self.hass,
            message,
            title=f"{NOTIFICATION_TITLE} - {self.portfolio_name}",
            notification_id=f"{DOMAIN}_{self.normalized_name}_error",
        )
