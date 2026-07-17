# Contributing

Thank you for helping improve SHARP COCORO AIR Taiwan support.

## Before opening an issue

- Confirm the issue still occurs on the latest release.
- Include the Home Assistant version, integration version, and exact SHARP
  model/region.
- Redact all app secrets, terminal IDs, box IDs, device IDs, ECHONET nodes,
  cookies, account details, and traffic captures.

## Local checks

Run these commands before submitting a pull request:

```bash
python3 -m compileall -q custom_components/sharp_cocoro_air tests
python3 -m unittest discover -s tests -v
python3 scripts/build_release.py
```

Keep cloud requests conservative and preserve the 60-second polling interval
unless there is evidence that a different interval is safe.
