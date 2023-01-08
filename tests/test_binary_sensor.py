"""Tests for the binary sensor module."""
import asyncio
import logging
import pytest

from datetime import timedelta
from homeassistant.const import (
    CONF_AUTHENTICATION,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_URL,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
    HTTP_BASIC_AUTHENTICATION,
    STATE_UNKNOWN,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_httpx import IteratorStream

from custom_components.nipca_custom.binary_sensor import NipcaMotionSensor, get_sensors
from custom_components.nipca_custom.const import (
    COMMON_INFO,
    MOTION_INFO,
    NOTIFY_STREAM,
    STREAM_INFO,
)
from custom_components.nipca_custom.nipca import NipcaDevice

from tests.conftest import TEST_URL

URL_INFO_LINES = (
    f"<root><device><presentationURL>{TEST_URL}</presentationURL></device></root>"
)

COMMON_INFO_LINES = """
model=DCS-2132LB1
brand=D-Link
product=Workshop
version=2.13
build=03
hw_version=B
nipca=1.9.5
name=Workshop
location=
macaddr=B0:C5:54:16:A5:21
ipaddr=192.168.100.63
netmask=255.255.255.0
gateway=192.168.100.1
ipaddr1_v6=
prefix1_v6=
gateway_v6=
wireless=yes
ptz=
focus=no
inputs=1
outputs=1
speaker=yes
videoout=no
pir=yes
icr=yes
ir=yes
mic=yes
led=yes
td=no
playing_music=no
whitelightled=no
"""

STREAM_INFO_LINES = """
videos=MJPEG,H.264
codeclist1=MJPEG,H.264
codeclist2=MJPEG,H.264
codeclist3=MJPEG,H.264
codeclist4=MJPEG
audios=G.711,AAC
aspectratios=16:9,4:3
resolutions=1280x720,800x448,640x360,480x272,320x176
resolutionlist1=1280x720,800x448,640x360,480x272,320x176
resolutionlist2=1280x720,800x448,640x360,480x272,320x176
resolutionlist3=640x360,320x176
resolutionlist4=640x360
vbitrates=4M,2M,1M,512K,256K,200K,128K,64K
qualitymodes=CBR,Fixquality
framerates=25,15,7,4,1
frameratelist1=25,15,7,4,1
frameratelist2=25,15,7,4,1
frameratelist3=25,15,7,4,1
frameratelist4=15
qualities=Excellent,Good,Standard
asamplerates=8
abitrates=64
micvol=0...1
cur_micvol=0
speakervol=1...10
cur_speakervol=7
vprofilenum=4
vprofile1=MJPEG
vprofileurl1=/video/mjpg.cgi?profileid=1
vprofileres1=800x448
vprofile2=H.264
vprofileurl2=/video/ACVS-H264.cgi?profileid=2
vprofileres2=1280x720
vprofile3=H.264
vprofileurl3=/video/ACVS-H264.cgi?profileid=3
vprofileres3=320x176
vprofile4=MJPEG
vprofileurl4=/video/mjpg.cgi?profileid=4
vprofileres4=640x360
aprofilenum=2
aprofile1=G.711
aprofileurl1=/audio/ACAS-ULAW.cgi
aprofile2=AAC
aprofileurl2=/audio/ACAS-AAC.cgi
vDprofileurl1=/av2/mjpg.cgi?profileid=1
vDprofileurl2=/av2/ACVS-H264.cgi?profileid=2
vDprofileurl3=/av2/ACVS-H264.cgi?profileid=3
vDprofileurl4=/av2/mjpg.cgi?profileid=4
aDprofileurl1=/av2/ACAS-ULAW.cgi
aDprofileurl2=/av2/ACAS-AAC.cgi
vban=1|-|1280x720|25|-|-:3|-|800x448,1280x720|-|-|-:3|-|640x360|25|-|-:3|-|-|-|-|6144,8192:3|-|480x272|-|-|-
"""

MOTION_INFO_LINES = """
enable=yes
mbmask=FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF
sensitivity=75
pir=yes
pir_sensitivity=50
"""

STREAM_LINES = b"""
md1=off
mdv1=0
pir=off
input1=off
recording=off
output1=off
speaker=on
speaker_occupied=off
mic=on
mic_muted=off
irled=off
led=on
audio_detected=off
audio_detect_val=14
cameraname=Workshop
"""


def test_get_binary_sensors():
    """Test parsing sensors attributes."""
    raw_data = {
        "model": "DCS-2132LB1",
        "brand": "D-Link",
        "product": "test",
        "version": "2.13",
        "build": "03",
        "hw_version": "B",
        "nipca": "1.9.5",
        "name": "test",
        "location": "",
        "macaddr": "01:23:45:67:89:0A",
        "ipaddr": "192.168.0.2",
        "netmask": "255.255.255.0",
        "gateway": "192.168.0.1",
        "ipaddr1_v6": "",
        "prefix1_v6": "",
        "gateway_v6": "",
        "wireless": "yes",
        "ptz": "",
        "focus": "no",
        "inputs": "1",
        "outputs": "1",
        "speaker": "yes",
        "videoout": "no",
        "pir": "yes",
        "icr": "yes",
        "ir": "yes",
        "mic": "yes",
        "led": "yes",
        "td": "no",
        "playing_music": "no",
        "whitelightled": "no",
        "videos": "MJPEG,H.264",
        "codeclist1": "MJPEG,H.264",
        "codeclist2": "MJPEG,H.264",
        "codeclist3": "MJPEG,H.264",
        "codeclist4": "MJPEG",
        "audios": "G.711,AAC",
        "aspectratios": "16:9,4:3",
        "resolutions": "1280x720,800x448,640x360,480x272,320x176",
        "resolutionlist1": "1280x720,800x448,640x360,480x272,320x176",
        "resolutionlist2": "1280x720,800x448,640x360,480x272,320x176",
        "resolutionlist3": "640x360,320x176",
        "resolutionlist4": "640x360",
        "vbitrates": "4M,2M,1M,512K,256K,200K,128K,64K",
        "qualitymodes": "CBR,Fixquality",
        "framerates": "25,15,7,4,1",
        "frameratelist1": "25,15,7,4,1",
        "frameratelist2": "25,15,7,4,1",
        "frameratelist3": "25,15,7,4,1",
        "frameratelist4": "15",
        "qualities": "Excellent,Good,Standard",
        "asamplerates": "8",
        "abitrates": "64",
        "micvol": "0...1",
        "cur_micvol": "0",
        "speakervol": "1...10",
        "cur_speakervol": "7",
        "vprofilenum": "4",
        "vprofile1": "MJPEG",
        "vprofileurl1": "/video/mjpg.cgi?profileid=1",
        "vprofileres1": "800x448",
        "vprofile2": "H.264",
        "vprofileurl2": "/video/ACVS-H264.cgi?profileid=2",
        "vprofileres2": "1280x720",
        "vprofile3": "H.264",
        "vprofileurl3": "/video/ACVS-H264.cgi?profileid=3",
        "vprofileres3": "320x176",
        "vprofile4": "MJPEG",
        "vprofileurl4": "/video/mjpg.cgi?profileid=4",
        "vprofileres4": "640x360",
        "aprofilenum": "2",
        "aprofile1": "G.711",
        "aprofileurl1": "/audio/ACAS-ULAW.cgi",
        "aprofile2": "AAC",
        "aprofileurl2": "/audio/ACAS-AAC.cgi",
        "vdprofileurl1": "/av2/mjpg.cgi?profileid=1",
        "vdprofileurl2": "/av2/ACVS-H264.cgi?profileid=2",
        "vdprofileurl3": "/av2/ACVS-H264.cgi?profileid=3",
        "vdprofileurl4": "/av2/mjpg.cgi?profileid=4",
        "adprofileurl1": "/av2/ACAS-ULAW.cgi",
        "adprofileurl2": "/av2/ACAS-AAC.cgi",
        "vban": "1|-|1280x720|25|-|-:3|-|800x448,1280x720|-|-|-:3|-|640x360|25|-|-:3|-|-|-|-|6144,8192:3|-|480x272|-|-|-",
        "enable": "yes",
        "mbmask": "FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF",
        "sensitivity": "75",
        "pir_sensitivity": "50",
    }
    result = get_sensors(raw_data)
    assert result == [
        ("motion", "md1"),
        ("sound", "audio_detected"),
        ("sound", "pir"),
        ("light", "led"),
        ("light", "irled"),
        (None, "input1"),
        (None, "output1"),
    ]


@pytest.mark.asyncio
async def test_binary_sensor_state(httpx_mock, hass):
    """Test binary sensors state update."""
    httpx_mock.add_response(url=TEST_URL, text=URL_INFO_LINES)
    httpx_mock.add_response(url=COMMON_INFO.format(TEST_URL), text=COMMON_INFO_LINES)
    httpx_mock.add_response(url=STREAM_INFO.format(TEST_URL), text=STREAM_INFO_LINES)
    httpx_mock.add_response(url=MOTION_INFO[0].format(TEST_URL), text=MOTION_INFO_LINES)
    httpx_mock.add_response(
        url=NOTIFY_STREAM.format(TEST_URL),
        stream=IteratorStream([STREAM_LINES]),
    )

    config = {
        CONF_URL: TEST_URL,
        CONF_AUTHENTICATION: HTTP_BASIC_AUTHENTICATION,
        CONF_USERNAME: "test",
        CONF_PASSWORD: "test",
        CONF_VERIFY_SSL: False,
        CONF_NAME: "NIPCA Custom",
        CONF_SCAN_INTERVAL: 10,
    }

    device = NipcaDevice(hass, config)
    await device.update_info()
    device.create_listener_task(hass)

    logger = logging.getLogger(__name__)
    coordinator = DataUpdateCoordinator(
        hass,
        logger,
        name="motion_sensor",
        update_method=device.update_motion_sensors,
        update_interval=timedelta(seconds=config.get(CONF_SCAN_INTERVAL)),
    )
    device._coordinator = coordinator
    sensors = [
        NipcaMotionSensor(hass, device, coordinator, sensor_name, sensor_class)
        for sensor_class, sensor_name in get_sensors(device._attributes)
    ]

    async def wait_until_events_come():
        while len(device._events) < 15:
            await asyncio.sleep(0.1)

    await coordinator.async_refresh()
    for sensor in sensors:
        assert sensor.is_on == STATE_UNKNOWN

    await wait_until_events_come()
    await coordinator.async_refresh()

    for sensor in sensors:
        assert sensor.state != STATE_UNKNOWN
        assert sensor.is_on != STATE_UNKNOWN
