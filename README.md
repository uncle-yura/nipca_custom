# NIPCA Custom Component for Home Assistant

[![](https://img.shields.io/github/license/uncle-yura/nipca_custom?style=for-the-badge)](LICENSE)
[![](https://img.shields.io/github/workflow/status/uncle-yura/nipca_custom/Python%20package?style=for-the-badge)](https://github.com/uncle-yura/nipca_custom/actions)

## About

Discover and set up NIPCA-compatible cameras.

## What It Is

This is a custom integration for Home Assistant that allows you to add cameras that support the NIPCA protocol. The integration adds a camera widget and camera sensors. Which sensors will be added depends on the camera. For example, if the camera has a PIR sensor, LED indicator, microphone, digital input, digital output, then all these sensors will be added. Also, if the camera is able to recognize movement in the image, then an image sensor will be added.

Some useful information about NIPCA: [NIPCA-API, Network IP Camera Application Programming Interface](http://gurau-audibert.hd.free.fr/josdblog/wp-content/uploads/2013/09/CGI_2121.pdf).

## Supported features

* UPNP discovery
* Auth
* Stream and attributes (name, motion detection status) discovery
* Motion, pir and sound detection
* Led, inputs and outputs status

## Supported devices

* D-Link DCS-2132LB `Firmware Version 2.13.03, Hardware Version B` *tested*

Most likely, other NIPСA cameras are also supported
* D-Link DCS-930LB1 `version=2.15 build=6`, `version=2.17 build=3`
* TRENDnet TV-IP672W, TV-IP672WI The Megapixel Wireless N (Day/Night) PTZ Internet Camera *[claimed1]*
* D-Link DCS-6513 *[claimed2]* and lot mote *[claimed3]*
* D-Link DCS-P6000LH *[implemented1]* (alternative location for motion config)

## Manual setup

To configure the component without using UPnP, use the following config:
```
binary_sensor:
- platform: nipca_custom
  username: "xxx"
  password: "xxx"
  url: "http://192.168.x.x/"
```

Optional:
* authentication: `basic` or `digest`, by default `basic`
* verify_ssl: `true` or `false`, by default `false`
* scan_interval: integer, by default 10 seconds
* name: string, config name, by default `NIPCA Custom`

## Debug component

To debug the component, use the following config:
```
logger:
  default: error
  logs:
    custom_components.nipca_custom: debug
```

## Running Tests

To run the test suite create a virtualenv (I recommend checking out [pyenv](https://github.com/pyenv/pyenv) and [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv) for this) and install the test requirements.

```bash
$ pip install -r dev-requirements.txt
```

After the test dependencies are installed you can simply invoke `pytest` to run
the test suite.

```bash
$ pytest
Test session starts (platform: darwin, Python 3.9.7, pytest 7.1.2, pytest-sugar 0.9.5)
rootdir: /Users/work/WorkProjects/hass_nipca, configfile: setup.cfg, testpaths: tests
plugins: anyio-3.6.1, xdist-2.5.0, freezegun-0.4.2, forked-1.4.0, requests-mock-1.9.2, homeassistant-custom-component-0.11.2, sugar-0.9.5, timeout-2.1.0, test-groups-1.0.3, respx-0.19.2, aiohttp-0.3.0, socket-0.5.1, cov-3.0.0, httpx-0.21.0
collecting ... 
 tests/test_binary_sensor.py ✓✓                                                                                                             12% █▎        
 tests/test_config_flow.py ✓✓✓✓✓✓✓✓                                                                                                         59% █████▉    
 tests/test_nipca.py ✓✓✓✓✓✓✓                                                                                                               100% ██████████
==================================================================== warnings summary ====================================================================
venv/lib/python3.9/site-packages/_pytest/config/__init__.py:1198
  /Users/work/WorkProjects/hass_nipca/venv/lib/python3.9/site-packages/_pytest/config/__init__.py:1198: PytestRemovedIn8Warning: The --strict option is deprecated, use --strict-markers instead.
    self.issue_config_time_warning(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html

---------- coverage: platform darwin, python 3.9.7-final-0 -----------
Name                                              Stmts   Miss  Cover   Missing
-------------------------------------------------------------------------------
custom_components/__init__.py                         0      0   100%
custom_components/nipca_custom/__init__.py           18      0   100%
custom_components/nipca_custom/binary_sensor.py      68      0   100%
custom_components/nipca_custom/camera.py             13      0   100%
custom_components/nipca_custom/config_flow.py        32      0   100%
custom_components/nipca_custom/const.py              11      0   100%
custom_components/nipca_custom/nipca.py             109      0   100%
-------------------------------------------------------------------------------
TOTAL                                               251      0   100%

Required test coverage of 93.0% reached. Total coverage: 100.00%

Results (1.06s):
      17 passed
```

## References and sources

* Atsuko Ito : <https://github.com/yottatsa/hass_nipca>