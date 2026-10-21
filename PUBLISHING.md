# Publishing checklist

The repository files are prepared for `gg50202gg/ha-sharp-cocoro-air`.

## One-time GitHub setup

1. Authenticate GitHub CLI:

   ```bash
   gh auth login -h github.com
   ```

2. From this directory, create the repository:

   ```bash
   git init -b main
   git add .
   git commit -m "Initial SHARP COCORO AIR Home Assistant integration"
   gh repo create gg50202gg/ha-sharp-cocoro-air \
     --public \
     --source=. \
     --remote=origin \
     --push \
     --description="Unofficial Home Assistant integration for SHARP COCORO AIR Taiwan"
   ```

3. In GitHub repository settings:

   - Keep **Issues** enabled.
   - Enable **Private vulnerability reporting**.
   - Add topics: `home-assistant`, `hacs`, `custom-integration`, `sharp`,
     `cocoro-air`, `taiwan`.

The repository must remain public for HACS custom repository installation.

## Publish version 0.1.4

Wait for the Validate workflow to pass, then create and push a matching tag:

```bash
git tag v0.1.4
git push origin v0.1.4
```

The Release workflow verifies that the tag matches `manifest.json`, builds
`sharp_cocoro_air.zip`, and creates a full GitHub Release. HACS uses published
GitHub Releases for version selection; a tag by itself is not enough.

## Future releases

1. Update the version in
   `custom_components/sharp_cocoro_air/manifest.json`.
2. Add release notes to `CHANGELOG.md`.
3. Run the local tests and `python3 scripts/build_release.py`.
4. Commit and push the changes.
5. Tag the exact manifest version with a leading `v`.
