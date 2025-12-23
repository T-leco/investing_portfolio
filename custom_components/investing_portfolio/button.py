"""Button platform for Investing Portfolio integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import normalize_portfolio_name
from .const import DOMAIN, CONF_PORTFOLIO_ID, CONF_PORTFOLIO_NAME, DEFAULT_PORTFOLIO_ID
from .coordinator import InvestingDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    coordinator: InvestingDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    portfolio_id = config_entry.data.get(CONF_PORTFOLIO_ID, DEFAULT_PORTFOLIO_ID)
    portfolio_name = config_entry.data.get(CONF_PORTFOLIO_NAME, f"Portfolio {portfolio_id}")
    normalized_name = normalize_portfolio_name(portfolio_name)
    
    async_add_entities([
        ActualizarInvestingButton(coordinator, config_entry, portfolio_name, normalized_name)
    ])


class ActualizarInvestingButton(CoordinatorEntity[InvestingDataCoordinator], ButtonEntity):
    """Button to force a data refresh.
    
    Entity ID: button.actualizar_investing_{normalized_name}
    """

    _attr_device_class = ButtonDeviceClass.UPDATE
    _attr_has_entity_name = False
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        coordinator: InvestingDataCoordinator,
        config_entry: ConfigEntry,
        portfolio_name: str,
        normalized_name: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._portfolio_name = portfolio_name
        self._attr_name = f"Update Investing {portfolio_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_update_investing"
        self.entity_id = f"button.update_investing_{normalized_name}"
        
        # Device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Investing {portfolio_name}",
            manufacturer="Investing.com",
            model="Portfolio Tracker",
            sw_version="1.0.0",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Manual refresh triggered for portfolio: %s", self._portfolio_name)
        await self.coordinator.async_force_refresh()
