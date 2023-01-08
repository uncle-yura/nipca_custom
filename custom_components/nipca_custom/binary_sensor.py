from datetime import timedelta
import logging

from homeassistant.components.binary_sensor import ENTITY_ID_FORMAT, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import async_generate_entity_id
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN
from .nipca import NipcaDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    config = hass.data[DOMAIN][config_entry.entry_id]
    if config_entry.options:
        config.update(config_entry.options)

    device = NipcaDevice(hass, config)
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
        return " ".join(
            [self._device._attributes.get("name", ""), self._name, "sensor"]
        )

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
        if (
            self._device.motion_detection_enabled
            and self._name in self._coordinator.data
        ):
            return self._coordinator.data[self._name]
        else:
            return STATE_UNKNOWN

    @property
    def extra_state_attributes(self):
        """Return the attributes of the binary sensor."""
        attr = self._device._events.copy()
        return {k: v for k, v in attr.items() if k.startswith(self._name[:2])}
