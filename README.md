# Home Assistant GPSLive Integration

GPSLive Tracker polls the GPSLive cloud API once per minute and adds a GPS device tracker and six sensors for each tracker: odometer, speed, tracker battery, car battery voltage, status and ignition.

**Version: 0.1.0** · **Home Assistant: 2025.5.0 or later** · **Cloud polling**

The built-in [Marketplace](https://contributors.home-assistant.io/marketplace/) is available from Home Assistant 2026.11. On earlier versions, use HACS. Local brand images are displayed from Home Assistant 2026.3.

## Install with Marketplace or HACS

The repository must be public before either service can download it. Until it is accepted into the shared catalog, add `https://github.com/haveyourphil/homeassistant-gpslive` as a custom repository, with category **Integration**.

[![Open GPSLive in HACS or Marketplace](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=haveyourphil&repository=homeassistant-gpslive&category=integration)

1. Download GPSLive Tracker from the repository page.
2. Restart Home Assistant if prompted. Restart after replacing an already loaded copy.
3. For a new installation, go to **Settings → Devices & services → Add integration → GPSLive Tracker**, and enter the API key generated in GPSLive.

[![Add GPSLive Tracker](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=gpslive)

One config entry supplies all trackers returned by the key. The key is stored in Home Assistant's config entry; it is never used as an entity or config-entry identifier.

## Replace an existing manual installation

**Keep the existing GPSLive config entry. Do not delete it or add the integration again.**

1. Take a Home Assistant backup, including its configuration and recorder database.
2. Download the managed copy into the existing `custom_components/gpslive/` location using Marketplace or HACS.
3. Restart Home Assistant and check the existing devices and entities.

This update keeps the `gpslive` domain, device identifiers `(gpslive, IMEI)`, tracker unique IDs `IMEI`, and sensor unique IDs `IMEI_odometer`, `IMEI_speed`, `IMEI_tracker_battery`, `IMEI_car_battery`, `IMEI_status` and `IMEI_ignition`. Config-entry version 1 and the stored `api_key` remain valid. No registry migration is needed. Existing entity IDs, custom names, areas and history stay associated with those entities when Home Assistant's storage and database are retained.

Regression tests seed the original registry records and verify their identities through setup, unload and reload. A live upgrade on your own installation is still the final check.

## Manual installation

Copy the complete `custom_components/gpslive/` folder from a release into `<config>/custom_components/gpslive/`, then restart Home Assistant. Configure a new installation as above; keep an existing config entry when updating.

## API keys and troubleshooting

- To rotate a key, use **Reconfigure** on the existing GPSLive entry. Enter a key for the same account. GPSLive's device response has no account ID to verify that a replacement key belongs to the original account.
- A rejected key starts Home Assistant's reauthentication flow. Update it there without deleting the entry.
- Connection errors, timeouts, invalid responses and server errors make entities unavailable until a successful poll. First-setup connection failures are retried automatically.
- A tracker absent from a successful response becomes unavailable; its registry records are retained. Trackers newly added in GPSLive appear after reloading the integration.
- Missing telemetry is shown as unknown. Speed remains in mph and odometer in miles, matching the existing integration.
- Download diagnostics from the integration menu for operational counts and status. Diagnostics exclude API keys, IMEIs, VINs, names, coordinates and raw API responses.

Report bugs through [GitHub Issues](https://github.com/haveyourphil/homeassistant-gpslive/issues). Never attach an API key or an unredacted GPSLive response. GPSLive API access is required; see the [API documentation](https://api.gpslive.app/api-docs/v1).

To remove GPSLive completely, delete its entry under Devices & services, then remove the downloaded integration in Marketplace/HACS and restart. Deleting the entry also removes its registered entities and is unnecessary when upgrading.

## Development and releases

Use Python 3.14.2 or later for the current test environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/ruff check .
.venv/bin/ruff format --check .
.venv/bin/python -m pytest
```

GitHub Actions runs hassfest, the HACS integration validator, linting and regression tests. See [the audit](docs/marketplace-audit.md) for compatibility decisions, validation and the publication checklist, and [release instructions](docs/releases.md) for publishing updates. No GitHub release has been created by this update.

## License

[MIT](LICENSE), copyright 2025-2026 Phil Smith.
