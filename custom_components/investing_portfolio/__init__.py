"""The Investing Portfolio integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    CONF_X_TOKEN,
    CONF_X_UDID,
    CONF_PORTFOLIO_ID,
    CONF_PORTFOLIO_NAME,
    DEFAULT_PORTFOLIO_ID,
)
from .coordinator import InvestingDataCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry to new version."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # Migrate from v1 (manual token entry) to v2 (login flow with portfolio_name)
        new_data = {**config_entry.data}
        
        # Add portfolio_name if not present (use entry title or generate from ID)
        if CONF_PORTFOLIO_NAME not in new_data:
            # Use the entry title as portfolio name (it was "Portfolio {id}" in v1)
            portfolio_id = new_data.get(CONF_PORTFOLIO_ID, DEFAULT_PORTFOLIO_ID)
            new_data[CONF_PORTFOLIO_NAME] = config_entry.title or f"Portfolio {portfolio_id}"
        
        hass.config_entries.async_update_entry(
            config_entry, 
            data=new_data, 
            version=2
        )
        _LOGGER.info(
            "Migration to version 2 successful for %s", 
            new_data.get(CONF_PORTFOLIO_NAME)
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Investing Portfolio from a config entry."""
    x_token = entry.data[CONF_X_TOKEN]
    x_udid = entry.data[CONF_X_UDID]
    portfolio_id = entry.data.get(CONF_PORTFOLIO_ID, DEFAULT_PORTFOLIO_ID)
    portfolio_name = entry.data.get(CONF_PORTFOLIO_NAME, f"Portfolio {portfolio_id}")

    coordinator = InvestingDataCoordinator(
        hass,
        x_token=x_token,
        x_udid=x_udid,
        portfolio_id=portfolio_id,
        portfolio_name=portfolio_name,
        options=dict(entry.options),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register options update listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
