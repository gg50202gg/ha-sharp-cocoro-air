# Changelog

All notable changes to this project are documented here.

## [0.1.4] - 2026-10-21

### Fixed

- Wait five seconds asynchronously after sending a power-on command before
  setting a preset or refreshing status, allowing the purifier to accept the
  next command. Already-on devices do not incur this delay.

### Added

- Regression coverage for command ordering, already-on preset changes, and
  failed power commands.

## [0.1.3] - 2026-10-21

### Fixed

- Accept positional percentage and preset arguments in the fan turn-on method,
  matching Home Assistant's fan service handler. Previously, turning on the fan
  raised a TypeError before sending a cloud command.

### Added

- Regression tests for positional turn-on calls, preset forwarding, and avoiding
  redundant power commands when already on.

## [0.1.2] - 2026-10-21

### Fixed

- Login API errors now reach the config flow as authentication failures rather
  than generic errors. Transport failures remain connection errors.
- Malformed JSON and invalid response text are handled as API errors rather
  than escaping the integration's error handling.
- Connection error messages no longer include transport exception URLs, which
  may contain connection credentials. API error payloads are not echoed.

### Added

- Ten mocked request tests covering login failures, malformed responses,
  timeouts, credential-safe errors, and bounded authentication retries.

## [0.1.1] - 2026-07-17

### Changed

- Sensor display precision is limited to two decimal places.
- Cumulative energy state values are rounded to two decimal places before they
  are stored by Home Assistant.

## [0.1.0] - 2026-07-17

### Added

- Initial HACS-compatible repository layout.
- Power control and seven FP-S90T-W operating modes.
- Temperature, humidity, power, and cumulative energy sensors.
- Config flow, YAML import, Traditional Chinese translations, and 60-second
  coordinated cloud polling.
