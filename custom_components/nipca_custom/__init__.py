"""NIPCA Component."""
import asyncio
from datetime import timedelta

from homeassistant import config_entries, core
from homeassistant.const import CONF_SCAN_INTERVAL
from .const import NIPCA_DOMAIN


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(NIPCA_DOMAIN, {})
    hass_data = dict(entry.data)

    if scan_interval := hass_data.pop(CONF_SCAN_INTERVAL):
        hass_data[CONF_SCAN_INTERVAL] = timedelta(seconds=scan_interval)

    hass.data[NIPCA_DOMAIN][entry.entry_id] = hass_data

    # Forward the setup to the sensor platform.
    await hass.config_entries.async_forward_entry_setups(entry, ["binary_sensor", "camera"])
    return True


async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, "binary_sensor"),
                hass.config_entries.async_forward_entry_unload(entry, "camera"),
            ]
        )
    )

    # Remove config entry from domain.
    if unload_ok:
        hass.data[NIPCA_DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the NIPCA component from yaml configuration."""
    hass.data.setdefault(NIPCA_DOMAIN, {})
    return True
