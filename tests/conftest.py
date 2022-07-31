"""pytest fixtures."""
import pytest

TEST_URL = "http://test"
TEST_URL_PATTERN = r"http:\/\/test\/.*"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield
