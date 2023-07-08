"""Tests for the config flow."""
import re
import pytest

from unittest.mock import ANY, patch
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.nipca_custom import config_flow
from custom_components.nipca_custom.const import (
    DEFAULT_NAME,
    DOMAIN,
    SCAN_INTERVAL,
    STEP_CONFIG,
    STILL_IMAGE,
)

from tests.conftest import TEST_URL, TEST_URL_PATTERN
from tests.test_binary_sensor import URL_INFO_LINES


@pytest.mark.asyncio
async def test_validate_auth_valid(httpx_mock, hass):
    """Test no exception is raised for a valid path."""
    httpx_mock.add_response(url=TEST_URL, text=URL_INFO_LINES)
    httpx_mock.add_response(url=STILL_IMAGE.format(TEST_URL))
    response = await config_flow.is_valid_auth({CONF_URL: TEST_URL}, {}, hass)
    assert response is True


@pytest.mark.asyncio
async def test_validate_auth_invalid(httpx_mock, hass):
    """Test no exception is raised for a valid path."""
    httpx_mock.add_response(url=TEST_URL, status_code=404)
    response = await config_flow.is_valid_auth({CONF_URL: TEST_URL}, {}, hass)
    assert response is False


@pytest.mark.asyncio
@patch("custom_components.nipca_custom.config_flow.DLinkUPNPProfile.async_discover")
async def test_flow_user_init(async_discover, hass):
    """Test the initialization of the form in the first step of the config flow."""
    async_discover.return_value = [{"LOCATION": "test"}]
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "user"}
    )
    expected = {
        "data_schema": ANY,
        "description_placeholders": None,
        "errors": None,
        "flow_id": ANY,
        "handler": "nipca_custom",
        "last_step": None,
        "step_id": "user",
        "type": "form",
    }

    assert expected == result
    assert CONF_NAME in result["data_schema"].schema
    assert CONF_URL in result["data_schema"].schema


@pytest.mark.asyncio
async def test_flow_auth_form(hass):
    """Test the initialization of the form in the second step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "auth"}
    )
    expected = {
        "data_schema": config_flow.AUTH_SCHEMA,
        "description_placeholders": None,
        "errors": {},
        "flow_id": ANY,
        "handler": "nipca_custom",
        "step_id": "auth",
        "last_step": None,
        "type": "form",
    }
    assert expected == result


@pytest.mark.asyncio
@patch("custom_components.nipca_custom.config_flow.is_valid_auth")
async def test_flow_auth_invalid(is_valid_auth, hass):
    """Test errors populated when auth is invalid."""
    is_valid_auth.return_value = False
    config_flow.NipcaConfigFlow.data = {}
    _result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": "auth"}
    )
    result = await hass.config_entries.flow.async_configure(
        _result["flow_id"], user_input={CONF_USERNAME: "bad", CONF_PASSWORD: "bad"}
    )
    assert {"base": "invalid_auth"} == result["errors"]


@pytest.mark.asyncio
async def test_flow_config_form(hass):
    """Test the initialization of the form in the third step of the config flow."""
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": STEP_CONFIG}
    )
    expected = {
        "data_schema": config_flow.get_config_schema(SCAN_INTERVAL),
        "description_placeholders": None,
        "errors": None,
        "flow_id": ANY,
        "handler": "nipca_custom",
        "step_id": STEP_CONFIG,
        "last_step": None,
        "type": "form",
    }
    assert expected == result


@pytest.mark.asyncio
async def test_options_flow_init(httpx_mock, hass):
    """Test config flow options."""
    httpx_mock.add_response(url=TEST_URL, text=URL_INFO_LINES)
    httpx_mock.add_response(url=re.compile(TEST_URL_PATTERN))

    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test_unique_id",
        data={
            CONF_URL: TEST_URL,
            CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
            CONF_USERNAME: "test",
            CONF_PASSWORD: "test",
            CONF_VERIFY_SSL: False,
            CONF_NAME: "NIPCA Custom",
            CONF_SCAN_INTERVAL: 10,
        },
        options={
            CONF_SCAN_INTERVAL: 5,
        },
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    # show initial form
    _result = await hass.config_entries.options.async_init(config_entry.entry_id)

    assert "form" == _result["type"]
    assert "init" == _result["step_id"]
    assert None is _result["errors"]

    result = await hass.config_entries.options.async_configure(
        _result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 5},
    )

    assert "create_entry" == result["type"]
    assert {"scan_interval": 5} == result["data"]

    # Unload the entry and verify that the data has been removed
    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.entry_id not in hass.data[DOMAIN]
