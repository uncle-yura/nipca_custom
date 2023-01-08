import logging
import voluptuous as vol

from typing import Callable
from datetime import timedelta
from homeassistant.helpers import config_validation as cv
from homeassistant.components.binary_sensor import ENTITY_ID_FORMAT, BinarySensorEntity, PLATFORM_SCHEMA
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.const import (
    CONF_SCAN_INTERVAL,
    STATE_ON,
    STATE_UNKNOWN,
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

from .const import DEFAULT_NAME, DOMAIN, SCAN_INTERVAL
from .nipca import NipcaDevice

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_AUTHENTICATION, default=HTTP_BASIC_AUTHENTICATION): vol.In(
            [HTTP_BASIC_AUTHENTICATION, HTTP_DIGEST_AUTHENTICATION]
        ),
        vol.Optional(CONF_VERIFY_SSL, default=False): cv.boolean,
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL): cv.positive_int,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Required(CONF_URL): cv.string,
    }
)


async def _setup_entities(
    hass: HomeAssistant, device: NipcaDevice, config: ConfigEntry, async_add_entities: Callable
):
    await device.update_info()
    device.create_listener_task(hass)

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="motion_sensor",
        update_method=device.update_motion_sensors,
        update_interval=timedelta(seconds=config.get(CONF_SCAN_INTERVAL)),
    )
    device._coordinator = coordinator
    await coordinator.async_refresh()

    async_add_entities(
        NipcaMotionSensor(hass, device, coordinator, sensor_name, sensor_class)
        for sensor_class, sensor_name in get_sensors(device._attributes)
    )


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: Callable,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)
    device = NipcaDevice(hass, config)
    await _setup_entities(hass, device, config, async_add_entities)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    device = NipcaDevice(hass, config)
    device.url = config.get(CONF_URL, "")
    await _setup_entities(hass, device, config, async_add_entities)


def get_sensors(attributes: dict) -> list:
    sensors = [("motion", "md1")]
    if attributes.get("mic") == "yes":
        sensors.append(("sound", "audio_detected"))

    if attributes.get("pir") == "yes":
        sensors.append(("sound", "pir"))

    if attributes.get("led") == "yes":
        sensors.append(("light", "led"))

    if attributes.get("ir") == "yes":
        sensors.append(("light", "irled"))

    num_inputs = int(attributes.get("inputs", 0))
    for input in range(1, num_inputs + 1):
        sensors.append((None, f"input{input}"))

    num_outputs = int(attributes.get("outputs", 0))
    for output in range(1, num_outputs + 1):
        sensors.append((None, f"output{output}"))

    return sensors


class NipcaMotionSensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, hass, device, coordinator, name, device_class):
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._hass: HomeAssistant = hass
        self._device: NipcaDevice = device
        self._name: str = name
        self._coordinator: DataUpdateCoordinator = coordinator
        self._attr_device_class: str = device_class

        self.entity_id = async_generate_entity_id(
            ENTITY_ID_FORMAT,
            self.unique_id,
            hass=hass,
        )

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return "_".join(
            [
                self._device._attributes.get("macaddr", "").replace(".", "_"),
                self._name,
                "sensor",
            ]
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return " ".join([self._device._attributes.get("name", ""), self._name, "sensor"])

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        if self._name in self._coordinator.data:
            return self._coordinator.data[self._name] == STATE_ON
        else:
            return STATE_UNKNOWN

    @property
    def state(self):
        """Return the state of the binary sensor."""
        if self._device.motion_detection_enabled and self._name in self._coordinator.data:
            return self._coordinator.data[self._name]
        else:
            return STATE_UNKNOWN

    @property
    def extra_state_attributes(self):
        """Return the attributes of the binary sensor."""
        attr = self._device._events.copy()
        return {k: v for k, v in attr.items() if k.startswith(self._name[:2])}
