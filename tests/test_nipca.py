"""Tests for the nipca module."""
from asyncio import CancelledError
import re

from anyio import ClosedResourceError
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_URL,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
    HTTP_BASIC_AUTHENTICATION,
    HTTP_DIGEST_AUTHENTICATION,
)
from httpx import ReadTimeout
import pytest

from custom_components.nipca_custom.const import (
    COMMON_INFO,
    MOTION_INFO,
    NOTIFY_STREAM,
    STREAM_INFO,
)
from custom_components.nipca_custom.nipca import NipcaDevice

from tests.conftest import TEST_URL, TEST_URL_PATTERN
from tests.test_binary_sensor import (
    COMMON_INFO_LINES,
    MOTION_INFO_LINES,
    STREAM_INFO_LINES,
    URL_INFO_LINES,
)


async def test__get_attributes_raise(httpx_mock, hass):
    """Test nipca _get_attribytes raise error."""
    httpx_mock.add_response(url=TEST_URL, text=URL_INFO_LINES)
    httpx_mock.add_response(url=re.compile(TEST_URL_PATTERN), status_code=404)

    config = {
        CONF_URL: TEST_URL,
    }

    device = NipcaDevice(hass, config)
    device.url = await device.get_presentation_url()
    assert await device._get_attributes(COMMON_INFO) == {}


async def test_nipca_listener_cancel(httpx_mock, hass):
    """Test event listener cancellation."""
    httpx_mock.add_response(url=TEST_URL, text=URL_INFO_LINES)
    httpx_mock.add_response(url=re.compile(TEST_URL_PATTERN))

    config = {
        CONF_URL: TEST_URL,
        CONF_AUTHENTICATION: HTTP_DIGEST_AUTHENTICATION,
        CONF_USERNAME: "test",
        CONF_PASSWORD: "test",
        CONF_NAME: "test",
    }

    device = NipcaDevice(hass, config)
    await device.update_info()
    device.create_listener_task(hass)
    assert not device._listener.done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP, True)
    await hass.async_block_till_done()
    assert device._listener.done()


@pytest.mark.parametrize(
    "error",
    [CancelledError, ConnectionError, ClosedResourceError, TimeoutError, ReadTimeout],
)
async def test_nipca_listener_errors(error, httpx_mock, hass):
    """Test event listener cancellation."""
    httpx_mock.add_response(url=TEST_URL, text=URL_INFO_LINES)
    httpx_mock.add_response(url=COMMON_INFO.format(TEST_URL), text=COMMON_INFO_LINES)
    httpx_mock.add_response(url=STREAM_INFO.format(TEST_URL), text=STREAM_INFO_LINES)
    httpx_mock.add_response(url=MOTION_INFO[0].format(TEST_URL), text=MOTION_INFO_LINES)
    httpx_mock.add_exception(url=NOTIFY_STREAM.format(TEST_URL), exception=error)

    config = {
        CONF_URL: TEST_URL,
        CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
        CONF_USERNAME: "test",
        CONF_PASSWORD: "test",
        CONF_NAME: "test",
    }

    device = NipcaDevice(hass, config)
    await device.update_info()
    assert await device._notify_listener() is False
