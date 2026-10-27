# Publishing GPSLive releases

The manifest and README use **1.0.0**. This is the first stable public version of the Marketplace/HACS-ready integration; there are no existing GitHub releases.

## First publication

1. Review [the security findings and compatibility notes](marketplace-audit.md). The code is licensed under [MIT](../LICENSE); confirm permission to redistribute the existing GPSLive artwork.
2. Confirm linting, tests, hassfest and HACS validation pass on the public repository.
3. Back up your Home Assistant installation and replace the manual copy while keeping its config entry. Restart and check the original entity IDs, device assignment, history, API key and reload behavior.
4. If publishing a release, create the tag **`1.0.0`** on the tested commit. The validation workflow checks tag/manifest agreement. Publish a GitHub Release from that tag; a tag without a published Release does not provide the recommended release-based update channel.
5. Add the public repository to Marketplace/HACS as an **Integration** custom repository and verify installation. For wider discovery, submit it to the `integration` list in [hacs/default](https://github.com/hacs/default), following the [catalog guide](https://contributors.home-assistant.io/marketplace/guides/catalog/).

Releases use the repository archive; no ZIP asset or build step is needed. A custom repository can also be installed directly from the default branch without publishing a release.

## Future updates

Update `manifest.json` and the README together, test, and publish a new matching tag and GitHub Release when using release-based updates, for example manifest `1.0.1` and tag `1.0.1`. Never replace an already published tag with different code. Write user-facing release notes, especially when a restart or newer Home Assistant is required. Use GitHub's pre-release flag for opt-in testing.

`hacs.json` declares Home Assistant **2025.5.0** as the minimum supported version. Increase this only when the code requires it, and test the new minimum. Marketplace itself starts with Home Assistant 2026.11; HACS supports installations on older Home Assistant versions. Brand images require 2026.3 and do not affect runtime functionality on older versions.

See the official [releases and updates guide](https://contributors.home-assistant.io/marketplace/guides/releases/).

## Suggested first release notes

GPSLive can now be installed and updated through Marketplace/HACS. Back up Home Assistant, download the managed copy over `custom_components/gpslive/`, and restart. **Keep your existing GPSLive config entry.** Domain, device identifiers, entity unique IDs, names, units and stored API key are preserved.

This release fixes unloading, shares Home Assistant's HTTP session, handles API and authentication failures, and adds key rotation and privacy-preserving diagnostics. Missing trackers become unavailable while retaining their registry records. New trackers require an integration reload. Only one new config entry is allowed; existing entries are not deleted or migrated.
