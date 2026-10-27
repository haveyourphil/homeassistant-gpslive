# Publishing GPSLive releases

The manifest and README use **0.1.0**. This retains the working integration's existing manifest version. The old README's `1.0` was inconsistent; there are no existing release tags in the checkout. Keeping the pre-1.0 version is appropriate while the first public release and live upgrade are being validated. Version 1.0.0 can follow when that stability commitment is intentional.

## First publication

1. Review [the security findings and compatibility notes](marketplace-audit.md). The code is licensed under [MIT](../LICENSE); confirm permission to redistribute the existing GPSLive artwork.
2. Commit and push the changes. Keep the repository private until you are ready to publish it. Set a useful GitHub description and topics such as `home-assistant`, `custom-integration`, `gpslive` and `gps-tracker`, and enable Issues and Actions.
3. Confirm linting, tests and hassfest pass. The HACS validator reads the GitHub repository and requires public access and repository metadata; run it again after making the repository public yourself. Do not skip its checks to obtain a passing result.
4. Back up your Home Assistant installation and replace the manual copy while keeping its config entry. Restart and check the original entity IDs, device assignment, history, API key and reload behavior.
5. Create the tag **`0.1.0`** on the tested commit. The validation workflow checks tag/manifest agreement. Publish a GitHub Release from that tag with the changes and upgrade instructions below. A tag without a published Release does not provide the recommended update channel.
6. Add the public repository to Marketplace/HACS as an **Integration** custom repository and verify installation. For wider discovery, submit it to the `integration` list in [hacs/default](https://github.com/hacs/default), following the [catalog guide](https://contributors.home-assistant.io/marketplace/guides/catalog/), with passing hassfest/HACS runs and the release link.

Releases use the repository archive; no ZIP asset or build step is needed. Neither repository visibility nor GitHub releases are changed automatically by this project.

## Future updates

Update `manifest.json` and the README together, test, and publish a new matching tag and GitHub Release, for example manifest `0.1.1` and tag `0.1.1`. Never replace an already published tag with different code. Write user-facing release notes, especially when a restart or newer Home Assistant is required. Use GitHub's pre-release flag for opt-in testing.

`hacs.json` declares Home Assistant **2025.5.0** as the minimum supported version. Increase this only when the code requires it, and test the new minimum. The version constraint is enforced for releases, so publish a release before relying on it. Marketplace itself starts with Home Assistant 2026.11; HACS supports installations on older Home Assistant versions. Brand images require 2026.3 and do not affect runtime functionality on older versions.

See the official [releases and updates guide](https://contributors.home-assistant.io/marketplace/guides/releases/).

## Suggested first release notes

GPSLive can now be installed and updated through Marketplace/HACS. Back up Home Assistant, download the managed copy over `custom_components/gpslive/`, and restart. **Keep your existing GPSLive config entry.** Domain, device identifiers, entity unique IDs, names, units and stored API key are preserved.

This release fixes unloading, shares Home Assistant's HTTP session, handles API and authentication failures, and adds key rotation and privacy-preserving diagnostics. Missing trackers become unavailable while retaining their registry records. New trackers require an integration reload. Only one new config entry is allowed; existing entries are not deleted or migrated.
