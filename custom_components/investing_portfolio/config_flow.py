"""Config flow for Investing Portfolio integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import InvestingAPI, AuthenticationError, PortfolioError, generate_x_udid, normalize_portfolio_name
from .const import (
    DOMAIN,
    CONF_EMAIL,
    CONF_X_TOKEN,
    CONF_X_UDID,
    CONF_PORTFOLIO_ID,
    CONF_PORTFOLIO_NAME,
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
)

_LOGGER = logging.getLogger(__name__)

# Step 1: Login credentials
STEP_LOGIN_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required("password"): str,
    }
)


def get_instance_id(hass: HomeAssistant) -> str:
    """Get Home Assistant instance ID for deterministic x-udid generation."""
    try:
        # Try to get the Home Assistant UUID from the system
        from homeassistant.helpers.instance_id import async_get
        # This is async so we can't use it directly here
        # Fall back to using configuration directory as seed
        return str(hass.config.config_dir)
    except Exception:
        return None


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Investing Portfolio."""

    VERSION = 2  # Incremented due to new data structure

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._x_token: str | None = None
        self._x_udid: str | None = None
        self._email: str | None = None
        self._portfolios: list[dict] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the login step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            email = user_input[CONF_EMAIL]
            password = user_input["password"]
            
            # Generate x-udid based on HA instance for consistency
            try:
                from homeassistant.helpers.instance_id import async_get
                instance_id = await async_get(self.hass)
                # Combine instance ID with email for unique but consistent UDID per account
                seed = f"{instance_id}:{email}"
            except Exception:
                seed = f"{self.hass.config.config_dir}:{email}"
            
            x_udid = generate_x_udid(seed)
            
            try:
                session = async_get_clientsession(self.hass)
                api = InvestingAPI(session)
                result = await api.login(email, password, x_udid)
                    
                self._x_token = result["token"]
                self._x_udid = x_udid
                self._email = email
                
                _LOGGER.info("Login successful, proceeding to portfolio selection")
                
                # Proceed to portfolio selection
                return await self.async_step_select_portfolio()
                
            except AuthenticationError as err:
                _LOGGER.error("Authentication failed: %s", err)
                errors["base"] = "invalid_auth"
            except Exception as err:
                _LOGGER.exception("Unexpected error during login: %s", err)
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_LOGIN_SCHEMA,
            errors=errors,
        )

    async def async_step_select_portfolio(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle portfolio selection step."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # User selected a portfolio
            portfolio_id = user_input["portfolio"]
            
            # Find the portfolio name from our cached list
            portfolio_name = None
            for p in self._portfolios:
                if p["portfolio_id"] == portfolio_id:
                    portfolio_name = p["portfolio_name"]
                    break
            
            if not portfolio_name:
                errors["base"] = "invalid_portfolio"
            else:
                # Check if this portfolio is already configured
                await self.async_set_unique_id(str(portfolio_id))
                self._abort_if_unique_id_configured()
                
                # Create the config entry
                return self.async_create_entry(
                    title=portfolio_name,
                    data={
                        CONF_EMAIL: self._email,
                        CONF_X_TOKEN: self._x_token,
                        CONF_X_UDID: self._x_udid,
                        CONF_PORTFOLIO_ID: portfolio_id,
                        CONF_PORTFOLIO_NAME: portfolio_name,
                    },
                )
        
        # Fetch available portfolios
        try:
            session = async_get_clientsession(self.hass)
            api = InvestingAPI(session)
            self._portfolios = await api.get_portfolios(
                self._x_token, 
                self._x_udid,
                position_only=True
            )
            
            if not self._portfolios:
                return self.async_abort(reason="no_portfolios")
            
            # Build portfolio options for dropdown
            portfolio_options = {
                p["portfolio_id"]: p["portfolio_name"] 
                for p in self._portfolios
            }
            
            return self.async_show_form(
                step_id="select_portfolio",
                data_schema=vol.Schema(
                    {
                        vol.Required("portfolio"): vol.In(portfolio_options),
                    }
                ),
                errors=errors,
            )
            
        except PortfolioError as err:
            _LOGGER.error("Failed to fetch portfolios: %s", err)
            errors["base"] = "cannot_connect"
            # Go back to login step
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_LOGIN_SCHEMA,
                errors=errors,
            )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Investing Portfolio."""
    
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_UPDATE_WEEKDAY_INTERVAL,
                        default=options.get(
                            CONF_UPDATE_WEEKDAY_INTERVAL, DEFAULT_UPDATE_WEEKDAY_INTERVAL
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
                    vol.Optional(
                        CONF_UPDATE_WEEKDAY_START,
                        default=options.get(
                            CONF_UPDATE_WEEKDAY_START, DEFAULT_UPDATE_WEEKDAY_START
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                    vol.Optional(
                        CONF_UPDATE_WEEKDAY_END,
                        default=options.get(
                            CONF_UPDATE_WEEKDAY_END, DEFAULT_UPDATE_WEEKDAY_END
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=0, max=23)),
                    vol.Optional(
                        CONF_UPDATE_NIGHT_TIME,
                        default=options.get(
                            CONF_UPDATE_NIGHT_TIME, DEFAULT_UPDATE_NIGHT_TIME
                        ),
                    ): str,
                    vol.Optional(
                        CONF_UPDATE_MORNING_TIME,
                        default=options.get(
                            CONF_UPDATE_MORNING_TIME, DEFAULT_UPDATE_MORNING_TIME
                        ),
                    ): str,
                }
            ),
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class InvalidPortfolio(HomeAssistantError):
    """Error to indicate invalid portfolio ID."""
