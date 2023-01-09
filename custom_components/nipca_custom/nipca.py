import xmltodict
import logging

from asyncio import CancelledError
from anyio import ClosedResourceError
from async_upnp_client.profiles.profile import UpnpProfileDevice
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    EVENT_HOMEASSISTANT_STOP,
    HTTP_BASIC_AUTHENTICATION,
    HTTP_DIGEST_AUTHENTICATION,
)
from homeassistant.core import HassJob
from homeassistant.helpers.httpx_client import get_async_client
from httpx import BasicAuth, DigestAuth, ReadTimeout, Timeout

from .const import (
    ASYNC_TIMEOUT,
    COMMON_INFO,
    MOTION_INFO,
    NOTIFY_STREAM,
    STILL_IMAGE,
    STREAM_INFO,
)

_LOGGER = logging.getLogger(__name__)


class DLinkUPNPProfile(UpnpProfileDevice):
    DEVICE_TYPES = [
        "urn:schemas-upnp-org:device:Basic:1",
    ]


class NipcaDevice:
    def __init__(self, hass: HassJob, config: dict) -> None:
        self.client = get_async_client(
            hass, verify_ssl=config.get(CONF_VERIFY_SSL, False)
        )
        self.hass = hass
        self.config = config

        username = config.get(CONF_USERNAME)
        password = config.get(CONF_PASSWORD)
        auth = config.get(CONF_AUTHENTICATION, HTTP_BASIC_AUTHENTICATION)
        if username and password:
            if auth == HTTP_DIGEST_AUTHENTICATION:
                self.auth = DigestAuth(username, password)
            else:
                self.auth = BasicAuth(username, password)
        else:
            self.auth = None

        self.url = ""
        self._listener = None
        self._coordinator = None
        self._events = {}
        self._attributes = {}

        hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, self.handle_stop_event)

    def handle_stop_event(self, *args, **kwargs):
        if self._listener and not self._listener.done():
            self._listener.cancel()

    def create_listener_task(self, hass: HassJob):
        self._listener = hass.loop.create_task(
            self._notify_listener(),
            name=self.get_task_name(),
        )

    def get_task_name(self):
        return f"nipca_{self.config[CONF_NAME]}_listener"

    async def get_presentation_url(self):
        response = await self.request(self.config[CONF_URL])
        device = xmltodict.parse(response.text)
        device_info = device["root"]["device"]
        return device_info.get("presentationURL")

    def get_request_params(self, url):
        return dict(
            method="GET", url=url, auth=self.auth, timeout=Timeout(ASYNC_TIMEOUT)
        )

    async def request(self, url):
        response = await self.client.request(**self.get_request_params(url))
        if response.status_code != 200:
            raise ConnectionError(response.reason_phrase)
        return response

    def stream(self, suffix):
        return self.client.stream(**self.get_request_params(suffix.format(self.url)))

    @property
    def mjpeg_url(self):
        return self.url + self._attributes.get("vprofileurl1", "")

    @property
    def still_image_url(self):
        return STILL_IMAGE.format(self.url)

    @property
    def motion_detection_enabled(self):
        """Return the camera motion detection status."""
        if (
            self._attributes.get("enable") == "yes"
            or self._attributes.get("motiondetectionenable") == "1"
        ):
            return True
        return False

    async def update_info(self):
        if not self.url:
            self.url = await self.get_presentation_url()

        self._attributes.update(await self._get_attributes(COMMON_INFO))
        self._attributes.update(await self._get_attributes(STREAM_INFO))
        for motion_url in MOTION_INFO:
            if attrs := await self._get_attributes(motion_url):
                self._attributes.update(attrs)
                break

    async def _get_attributes(self, suffix):
        url = suffix.format(self.url)
        result = {}
        try:
            response = await self.request(url)
        except ConnectionError as err:
            _LOGGER.debug("NIPCA ConnectionError: %s, %s", err, url)
        else:
            for l in response.iter_lines():
                result.update(self._parse_line(l))
        return result

    @staticmethod
    def _parse_line(l):
        if l and "=" in l:
            k, v = l.strip().split("=", 1)
            return {k.lower(): v}
        return {}

    async def update_motion_sensors(self):
        if not self._listener or (
            self._listener.done() and not self._listener.cancelled()
        ):
            self.create_listener_task(self.hass)
        return self._events

    async def _notify_listener(self):
        try:
            async with self.stream(NOTIFY_STREAM) as response:
                async for line in response.aiter_lines():
                    line = line.strip()
                    _LOGGER.debug("NIPCA received: %s", line)
                    self._events.update(self._parse_line(line))
        except CancelledError:
            _LOGGER.info("NIPCA listener task canceled")
        except (ConnectionError, ClosedResourceError):
            _LOGGER.warning("NIPCA listener connection error")
        except (TimeoutError, ReadTimeout):
            _LOGGER.warning("NIPCA listener task timeout")
        except Exception as error:
            _LOGGER.error("NIPCA listener unknown error: %s", error)
        else:
            return True
        return False
