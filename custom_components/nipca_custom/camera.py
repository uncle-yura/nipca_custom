from homeassistant import config_entries, core
from homeassistant.components.mjpeg.camera import MjpegCamera
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .nipca import NipcaDevice


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)

    device = NipcaDevice(hass, config)
    await device.update_info()

    async_add_entities(
        [
            MjpegCamera(
                name=config_entry.title,
                authentication=config[CONF_AUTHENTICATION],
                username=config[CONF_USERNAME],
                password=config[CONF_PASSWORD],
                mjpeg_url=device.mjpeg_url,
                still_image_url=device.still_image_url,
                verify_ssl=config[CONF_VERIFY_SSL],
                unique_id=config_entry.entry_id,
                device_info=DeviceInfo(
                    name=config[CONF_NAME],
                    identifiers={(DOMAIN, config_entry.entry_id)},
                ),
            )
        ]
    )
