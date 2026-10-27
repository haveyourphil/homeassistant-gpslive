# Marketplace and Home Assistant audit

Reviewed on 27 October 2026 against the official documentation linked below. The built-in Marketplace arrives in Home Assistant 2026.11 and uses the HACS catalog, `hacs.json` and validation action.

## Changes and compatibility

| Area | Result |
| --- | --- |
| Repository layout | One integration in `custom_components/gpslive/`, with root README, MIT `LICENSE`, `hacs.json`, development requirements, CI and release instructions. |
| Marketplace metadata | `hacs.json` contains only `name` and minimum `homeassistant: 2025.5.0`. Removed obsolete `domains`, `iot_class`, `render_readme`, invalid `country: global`, and the unnecessary default `content_in_root`. No `persistent_directory`: runtime data belongs to Home Assistant, outside this folder. |
| Manifest | Kept domain, integration name, config flow, cloud polling and version `0.1.0`. Added repository documentation/issues URLs, explicit `hub` type, tracker category and `single_config_entry`. Normalized the codeowner's casing. Removed the bundled `aiohttp` requirement and unused empty dependencies. |
| Branding | Moved the existing square 256×256 PNG to `brand/icon.png`, byte-for-byte unchanged. Removed the invalid manifest `branding` field. The icon also supplies the logo fallback. Older Home Assistant versions can load the code without displaying local branding. |
| Unload and reload | Both platforms are unloaded with `async_unload_platforms`; its success/failure is returned. The coordinator receives its config entry, so Home Assistant registers shutdown on unload and failed setup. The shared session remains open for Home Assistant to manage. |
| Runtime data | A typed `GPSLiveConfigEntry` stores its coordinator in `entry.runtime_data`, replacing `hass.data`. This is in-memory state, so no stored-data migration is needed. |
| API access | One shared HA aiohttp session, a 30-second request timeout, no redirects, and the existing endpoint/header authentication. HTTP 401/403 starts reauthentication; other non-200 responses, transport/JSON/encoding failures, malformed lists and missing/duplicate IMEIs become sanitized update errors. Empty device lists are valid. |
| Coordinator | Retains one-minute polling; first refresh validates setup, failures use HA retry/availability behavior, and unchanged responses avoid unnecessary updates. Exceptions omit credentials, response bodies and arbitrary exception text. No tracker IMEIs are logged by the integration. |
| Config flow | Validates the key before creating an entry, masks its form input, and supports reauth and reconfigure by updating/reloading the same entry. Empty keys are rejected. Existing entry data is merged, preserving other settings. |
| Entity robustness | Missing devices become unavailable without registry deletion; missing/malformed telemetry becomes unknown. Invalid/non-finite/out-of-range coordinates are ignored. Numeric conversions catch expected errors. Existing units, sensor classes and state classes are preserved. |
| Tracker battery | Uses the existing battery sensor and retains the legacy `battery_level` state attribute without overriding the deprecated tracker property. |
| Translations | Replaced the incomplete strings with a complete English `translations/en.json` for setup, errors and credential replacement. Removed unused `strings.json`; custom integrations ship finished translations. |
| Diagnostics | Returns only config-entry version, last-update success, device count and polling interval. Does not serialize entry data, exception objects or raw tracker data. |
| CI | Push/PR/nightly/manual hassfest and HACS integration validation, without ignored checks or PR comments. Ruff and regression tests run against current and minimum supported Home Assistant. Tag builds check exact tag/manifest version agreement. Dependabot monitors Actions and Python dependencies. |

The unused `api.py` had no callers or imports in the installed integration. It has been deleted, removing its blocking `requests.get()` and API-key query parameter.

### Identity contract

- Domain remains `gpslive`.
- Device identifiers remain `{("gpslive", IMEI)}`; manufacturer, model and VIN-based serial metadata are retained.
- Tracker unique ID remains the IMEI.
- Sensor unique IDs retain the six suffixes: `_odometer`, `_speed`, `_tracker_battery`, `_car_battery`, `_status`, `_ignition`.
- Existing naming behavior is retained, including full device-name prefixes. No `has_entity_name` conversion, binary-sensor conversion of ignition, unit correction or registry renaming was introduced.
- Config-entry version remains 1, with the API key still under `data["api_key"]`. No new config-entry unique ID is assigned.

The integration can replace a manual copy without deleting the config entry. Entity registry/history/configuration remain associated with the same IDs when HA storage and the recorder database are retained. Tests verify registry identity and custom settings; they do not replay a production recorder database or call a live GPSLive account.

### Account model

One entry already retrieves all trackers for a key. The existing API contract supplies device IMEIs, but no stable account identifier. Supporting multiple entries safely would need account discovery and handling overlapping device lists. The low-risk choice is `single_config_entry`, enforced by Home Assistant, without assigning a key-derived unique ID. Existing entries are neither removed nor migrated.

Reauthentication and reconfiguration validate API access but cannot prove the replacement key belongs to the same account. Use a key for the original account. A different account can make old trackers unavailable and expose new trackers on reload; it does not rewrite their IDs. The external GPSLive API documentation could not be retrieved during this audit, so no additional account endpoint was assumed.

## Validation

- **46 regression tests pass on Home Assistant 2025.5.0 and 2026.10.4**, with synthetic keys, IMEIs, vehicle metadata and coordinates against real Home Assistant config flows, registries and platform setup.
- Tests cover single-entry prevention; setup and credential errors; preserving entry data during reauth/reconfigure; HTTP statuses, malformed JSON/lists and transport failures; sanitized logging; initial setup retry and reauth; registry continuity through unload/reload; failed unload; partial telemetry; coordinate validation; disappearing devices; availability recovery; and diagnostics privacy.
- Current hassfest was run from Home Assistant Core `dev`, commit `69cc18db`, with **zero invalid integrations**. The official Docker image could not be pulled because the registry returned access denied; the source runner completed instead. The older 2026.10.4 hassfest rejects the new `categories` field, which is supported by the current validator documented for Marketplace. Current and minimum Home Assistant runtime tests accept the manifest.
- Ruff lint/format, JSON parsing, unchanged-logo comparison and `git diff --check` pass.
- The HACS action is configured but has not run against these unpushed local changes. Its GitHub checks, including public visibility, description, topics and Issues, must pass after publication. No checks are ignored to work around private repository access.
- A runtime test attempt against unreleased 2026.11 development code could not start: the latest released custom-integration test helper imports a logger helper removed in Core `dev`. The current hassfest checks completed on that source; runtime regression results above are for released HA versions. Repeat runtime tests with a matching 2026.11 helper when available, and check installation in Marketplace on the release/beta before announcing support as live-verified.

## Public repository security review

Gitleaks 8.30.1 scanned all local Git refs/history and the working directory with redacted reporting: **no credential leaks found**. Manual review covered current files, historical paths/text and the original image metadata. No real API keys, tokens, private keys, tracker locations, IMEIs, VINs, Home Assistant storage or environment-specific runtime files were found. Test credentials and tracker data are synthetic. Added ignore rules for Python/test output, local environments and `secrets.yaml`.

**Privacy finding:** Git commit author/committer metadata includes the maintainer's name and a personal email address, alongside a GitHub noreply address. Publishing the repository exposes that metadata. Decide whether to retain it or rewrite it before the first public release; no history was rewritten here. The artwork contains normal PNG display metadata, without identifying EXIF information.

No credential-related blocker to making the audited checkout public was found. This review cannot cover remote-only refs, GitHub artifacts, issues, or files outside the checkout. Repository settings were not changed. The owner selected the [MIT license](../LICENSE), which has been added to the repository.

## Scope decisions and remaining work

The Integration Quality Scale is used as guidance; no tier is claimed. Custom repairs would duplicate Home Assistant's built-in reauthentication and setup-retry flows, so none were added. Dynamic discovery of newly added trackers, configurable polling, account enumeration, more languages and extensive library extraction are disproportionate to this compatibility-focused update. Reload after adding trackers. Existing naming and sensor types take priority over cosmetic conformity.

The code retains the minimum **2025.5.0** rather than requiring 2026.11 merely for Marketplace. CI pins matching HA test helpers, and the minimum is tested separately. Local branding requires 2026.3; that is a UI capability difference only.

Before publishing: settle Git email privacy, push and validate, set repository description/topics/Issues, make the repository public yourself, perform a backed-up live upgrade, and publish the first matching tag and GitHub Release. See [release instructions](releases.md). Catalog submission is separate from installing a custom repository.

## Official references

- [Marketplace overview](https://contributors.home-assistant.io/marketplace/), [custom integrations](https://contributors.home-assistant.io/marketplace/guides/integrations/), [repository structure](https://contributors.home-assistant.io/marketplace/reference/repository-structure/) and [hacs.json](https://contributors.home-assistant.io/marketplace/reference/hacs-json/).
- [Validation and Actions](https://contributors.home-assistant.io/marketplace/reference/validation/), [releases](https://contributors.home-assistant.io/marketplace/guides/releases/) and [catalog submission](https://contributors.home-assistant.io/marketplace/guides/catalog/).
- [Manifest reference](https://developers.home-assistant.io/docs/creating_integration_manifest/), [brand images](https://contributors.home-assistant.io/core/integrations/brands/) and [categories](https://contributors.home-assistant.io/core/integrations/categories/).
- [Typed runtime data](https://contributors.home-assistant.io/core/quality-scale/runtime-data/), [coordinator lifecycle](https://contributors.home-assistant.io/core/integrations/fetching-data/) and [reauthentication/reconfiguration](https://contributors.home-assistant.io/core/integrations/reauth-reconfigure/).
- [Tracker battery deprecation](https://contributors.home-assistant.io/blog/2026/06/15/device-tracker-changes/).
