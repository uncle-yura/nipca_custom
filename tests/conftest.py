"""pytest fixtures."""
import pytest

TEST_URL = "http://test.local"
TEST_URL_PATTERN = r"http:\/\/test\.local\/.*"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield
