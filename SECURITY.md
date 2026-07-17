# Security policy

## Reporting a vulnerability

Do not open a public issue containing credentials, captured traffic, cookies,
account information, device identifiers, or a proof of concept that exposes a
user's purifier.

Use GitHub's private vulnerability reporting feature for the repository. If it
is not available yet, contact the repository owner privately before sharing
technical details.

## Sensitive values

The following values must be treated as credentials even if SHARP does not call
them passwords: `app_secret`, `terminal_app_id`, `box_id`, `device_id`, and
session cookies. Rotate or re-register the official app terminal if any of these
values are exposed.
