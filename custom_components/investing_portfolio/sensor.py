"""Sensor platform for Investing Portfolio integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CURRENCY_EURO, PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .api import normalize_portfolio_name
from .const import DOMAIN, CONF_PORTFOLIO_ID, CONF_PORTFOLIO_NAME, DEFAULT_PORTFOLIO_ID
from .coordinator import InvestingDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator: InvestingDataCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    portfolio_id = config_entry.data.get(CONF_PORTFOLIO_ID, DEFAULT_PORTFOLIO_ID)
    portfolio_name = config_entry.data.get(CONF_PORTFOLIO_NAME, f"Portfolio {portfolio_id}")
    normalized_name = normalize_portfolio_name(portfolio_name)
    
    sensors = [
        InvestingSensor(coordinator, config_entry, portfolio_name, normalized_name),
        OpenPLSensor(coordinator, config_entry, portfolio_name, normalized_name),
        OpenPLPercSensor(coordinator, config_entry, portfolio_name, normalized_name),
        DailyPLSensor(coordinator, config_entry, portfolio_name, normalized_name),
        DailyPLPercSensor(coordinator, config_entry, portfolio_name, normalized_name),
    ]
    async_add_entities(sensors)


class InvestingSensor(CoordinatorEntity[InvestingDataCoordinator], SensorEntity):
    """Sensor for investment portfolio value.
    
    Entity ID: sensor.investing_{normalized_name}
    State: Current market value of investments
    Attributes: openpl, openplperc, dailypl, dailyplperc, timestamp
    """

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = CURRENCY_EURO
    _attr_has_entity_name = False
    _attr_icon = "mdi:cash-multiple"

    def __init__(
        self,
        coordinator: InvestingDataCoordinator,
        config_entry: ConfigEntry,
        portfolio_name: str,
        normalized_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._portfolio_name = portfolio_name
        self._normalized_name = normalized_name
        self._attr_name = f"Investing {portfolio_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_investing"
        self.entity_id = f"sensor.investing_{normalized_name}"
        
        # Device registry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Investing {portfolio_name}",
            manufacturer="Investing.com",
            model="Portfolio Tracker",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> float | None:
        """Return the current market value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("market_value")

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return additional state attributes."""
        if self.coordinator.data is None:
            return {}
        
        return {
            "openpl": self.coordinator.data.get("open_pl"),
            "openplperc": self.coordinator.data.get("open_pl_perc"),
            "dailypl": self.coordinator.data.get("daily_pl"),
            "dailyplperc": self.coordinator.data.get("daily_pl_perc"),
            "timestamp": self.coordinator.data.get("timestamp"),
            "portfolio_id": self.coordinator.portfolio_id,
            "portfolio_name": self._portfolio_name,
        }


class OpenPLSensor(CoordinatorEntity[InvestingDataCoordinator], SensorEntity):
    """Sensor for open profit/loss (total change)."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = CURRENCY_EURO
    _attr_has_entity_name = False
    _attr_icon = "mdi:chart-line-variant"

    def __init__(
        self,
        coordinator: InvestingDataCoordinator,
        config_entry: ConfigEntry,
        portfolio_name: str,
        normalized_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Open PL {portfolio_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_openpl"
        self.entity_id = f"sensor.investing_{normalized_name}_openpl"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Investing {portfolio_name}",
            manufacturer="Investing.com",
            model="Portfolio Tracker",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> float | None:
        """Return the open P/L value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("open_pl")


class OpenPLPercSensor(CoordinatorEntity[InvestingDataCoordinator], SensorEntity):
    """Sensor for open profit/loss percentage."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_has_entity_name = False
    _attr_icon = "mdi:percent"

    def __init__(
        self,
        coordinator: InvestingDataCoordinator,
        config_entry: ConfigEntry,
        portfolio_name: str,
        normalized_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Open PL Perc {portfolio_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_openplperc"
        self.entity_id = f"sensor.investing_{normalized_name}_openplperc"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Investing {portfolio_name}",
            manufacturer="Investing.com",
            model="Portfolio Tracker",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> float | None:
        """Return the open P/L percentage."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("open_pl_perc")


class DailyPLSensor(CoordinatorEntity[InvestingDataCoordinator], SensorEntity):
    """Sensor for daily profit/loss."""

    _attr_device_class = SensorDeviceClass.MONETARY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_native_unit_of_measurement = CURRENCY_EURO
    _attr_has_entity_name = False
    _attr_icon = "mdi:calendar-today"

    def __init__(
        self,
        coordinator: InvestingDataCoordinator,
        config_entry: ConfigEntry,
        portfolio_name: str,
        normalized_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Daily PL {portfolio_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_dailypl"
        self.entity_id = f"sensor.investing_{normalized_name}_dailypl"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Investing {portfolio_name}",
            manufacturer="Investing.com",
            model="Portfolio Tracker",
            sw_version="1.0.0",
        )

    @property
    def native_value(self) -> float | None:
        """Return the daily P/L value."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("daily_pl")


class DailyPLPercSensor(CoordinatorEntity[InvestingDataCoordinator], SensorEntity):
    """Sensor for daily profit/loss percentage."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_has_entity_name = False
    _attr_icon = "mdi:percent"

    def __init__(
        self,
        coordinator: InvestingDataCoordinator,
        config_entry: ConfigEntry,
        portfolio_name: str,
        normalized_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_name = f"Daily PL Perc {portfolio_name}"
        self._attr_unique_id = f"{config_entry.entry_id}_dailyplperc"
        self.entity_id = f"sensor.investing_{normalized_name}_dailyplperc"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=f"Investing {portfolio_name}",
            manufacturer="Investing.com",
            model="Portfolio Tracker",
            sw_version="1.1.0",
        )

    @property
    def native_value(self) -> float | None:
        """Return the daily P/L percentage."""
        if self.coordinator.data is None:
            return None
        return self.coordinator.data.get("daily_pl_perc")
