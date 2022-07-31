import logging
from typing import Any, Dict, Optional

from homeassistant import config_entries, core
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
    HTTP_DIGEST_AUTHENTICATION,
)
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DEFAULT_NAME, DOMAIN, SCAN_INTERVAL, STEP_CONFIG, STILL_IMAGE
from .nipca import DLinkUPNPProfile, NipcaDevice

_LOGGER = logging.getLogger(__name__)

AUTH_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_USERNAME): cv.string,
        vol.Optional(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_AUTHENTICATION, default=HTTP_BASIC_AUTHENTICATION): vol.In(
            [HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION]
        ),
        vol.Optional(CONF_VERIFY_SSL, default=False): cv.boolean,
    }
)


def get_config_schema(scan_interval):
    return vol.Schema(
        {
            vol.Optional(CONF_SCAN_INTERVAL, default=scan_interval): cv.positive_int,
        }
    )


def get_discovery_schema(resps):
    return vol.Schema(
        {
            vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
            vol.Required(CONF_URL): vol.In([resp["LOCATION"] for resp in resps]),
        }
    )


async def is_valid_auth(auth_data: dict, data: dict, hass: core.HassJob):
    device = NipcaDevice(hass, dict(**data, **auth_data))
    try:
        url = await device.get_presentation_url()
        await device.request(STILL_IMAGE.format(url))
    except Exception as e:
        _LOGGER.error(e)
        return False
    return True


class NipcaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """NIPCA config flow."""

    data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Invoked when a user initiates a flow via the user interface."""

        if user_input is not None:
            self.data = user_input
            return await self.async_step_auth()

        resps = await DLinkUPNPProfile.async_discover()
        return self.async_show_form(
            step_id="user", data_schema=get_discovery_schema(resps)
        )

    async def async_step_auth(self, user_input: Optional[Dict[str, Any]] = None):
        """Second step in config flow to add a authentication."""

        errors: Dict[str, str] = {}
        if user_input is not None:
            if await is_valid_auth(user_input, self.data, self.hass):
                self.data.update(user_input)
                return await self.async_step_config()

            errors["base"] = "invalid_auth"

        return self.async_show_form(
            step_id="auth", data_schema=AUTH_SCHEMA, errors=errors
        )

    async def async_step_config(self, user_input: Optional[Dict[str, Any]] = None):
        """Third step in config flow to configure device."""

        if user_input is not None:
            self.data.update(user_input)
            return self.async_create_entry(title=self.data[CONF_NAME], data=self.data)

        config_schema = get_config_schema(SCAN_INTERVAL)
        return self.async_show_form(step_id=STEP_CONFIG, data_schema=config_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handles options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Manage the options for the NIPCA component."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        config_schema = get_config_schema(
            self.config_entry.options.get(
                CONF_SCAN_INTERVAL, self.config_entry.data[CONF_SCAN_INTERVAL]
            )
        )
        return self.async_show_form(step_id="init", data_schema=config_schema)
