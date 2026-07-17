# SHARP COCORO AIR Taiwan for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/)
[![Validate](https://github.com/gg50202gg/ha-sharp-cocoro-air/actions/workflows/validate.yml/badge.svg)](https://github.com/gg50202gg/ha-sharp-cocoro-air/actions/workflows/validate.yml)

Unofficial Home Assistant custom integration for the Taiwan SHARP COCORO AIR
cloud service. It was developed and tested with the **SHARP FP-S90T-W**.

> This project is not affiliated with or endorsed by SHARP. It uses an
> undocumented cloud API that may change without notice.

## Features

- Power on and off
- Auto, pollen, sleep, comfort, quiet, medium, and strong modes
- Temperature and humidity sensors
- Instantaneous power and cumulative energy sensors
- UI config flow and coordinated 60-second cloud polling
- Traditional Chinese and English entity translations

## Requirements

- Home Assistant 2026.7.0 or newer
- A Taiwan COCORO AIR device already registered in the official app
- Connection identifiers captured from your own official app session

The integration does not ask for your COCORO account password. The current
cloud login requires the app/terminal and device identifiers listed in the
config flow. Treat every captured value as a credential: never post it in an
issue, screenshot, log, or public repository.

## Install with HACS

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=gg50202gg&repository=ha-sharp-cocoro-air&category=integration)

Until this repository is accepted into the default HACS catalog, add it as a
custom repository:

1. Open HACS in Home Assistant.
2. Open **Custom repositories**.
3. Enter `https://github.com/gg50202gg/ha-sharp-cocoro-air`.
4. Select **Integration**, add the repository, and install it.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration** and search for
   `SHARP COCORO AIR (Taiwan)`.

## Manual GitHub installation

Download `sharp_cocoro_air.zip` from the latest GitHub Release and extract it
into the Home Assistant configuration directory. The final path must be:

```text
/config/custom_components/sharp_cocoro_air/manifest.json
```

Restart Home Assistant, then add the integration from **Devices & services**.

## Supported entities

| Entity | Description |
| --- | --- |
| Fan | Power and seven operating modes |
| Temperature | Room temperature reported by the purifier |
| Humidity | Relative humidity reported by the purifier |
| Power | Instantaneous power in watts |
| Energy | Cumulative energy in kWh |

## Privacy and security

- Communication is cloud polling over HTTPS; this is not local LAN control.
- Credentials are stored in the Home Assistant config entry.
- Debug logs and diagnostics must be reviewed before sharing.
- Do not commit captured sessions, traffic dumps, APKs, certificates, account
  details, or device identifiers.

## Known limitations

- Only FP-S90T-W on the Taiwan service has been verified.
- SHARP may change the private API at any time.
- Capturing the required identifiers is currently an advanced, manual step.
- The cloud may accept a command before its result endpoint reports a match;
  the integration refreshes device state after commands to confirm the result.

## Development

```bash
python3 -m compileall -q custom_components/sharp_cocoro_air tests
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) before submitting a change and
[SECURITY.md](SECURITY.md) for private vulnerability reports.

## License

MIT. See [LICENSE](LICENSE).
