# Home Assistant GPSLive Integration
---
**Title:** "GPSLive"

**Description:** "Integration that polls GPSLive for trackers"

**Version:** 1.0

**Date created:** 2025-07-08

**Last update:** 2025-07-23

---

## Configuration Options

- API Key: API Key generated in GPSLive

## Installation

### Option 1 (preferred)

Use [HACS](https://hacs.xyz/) to install
Add as [custom repository](https://hacs.xyz/docs/faq/custom_repositories) to HACS

### Option 2

1. Below config-folder create a new folder called`custom_components` if not already exist.
2. Below new `custom_components` folder create a new folder called `gpslive`
3. Upload the files/folders in `custom_components/gpslive` directory to the newly created folder.
4. Restart before proceeding

## Activate integration in HA

[![Add integrations](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=gpslive)

After installation go to "Devices & services" and then add a new integration.
