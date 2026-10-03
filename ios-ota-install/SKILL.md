---
name: ios-ota-install
description: Install a development build of an iOS app on your own phone over the air, from a Safari link served on your Tailscale tailnet. Use when asked to deploy, redeploy or install a build on the phone and the phone is not reachable by Xcode or devicectl (for example it is away from the Mac's Wi-Fi, or the device shows "unavailable"). Also covers what does and does not survive this route.
---

# iOS over-the-air install (Safari link on the tailnet)

Xcode and `devicectl` find phones by local-network discovery, which Tailscale does not carry, so
they cannot install over Tailscale (CoreDevice error 1011, device "unavailable"). This route works
instead: package the device-signed app as an IPA, serve an `itms-services` install page through
Tailscale Serve on the Mac, and send the user the link. They tap Install in Safari on the phone.

Only devices on the tailnet can open the link, and only devices in the app's provisioning
profile can install it. Nothing goes to Apple, TestFlight or the public internet. Never use
`tailscale funnel` for this.

## Requirements

- macOS with Xcode command-line tools (`xcodebuild`, `xcrun devicectl`, `codesign`, `security`).
- Tailscale running and logged in on both the Mac and the phone, with HTTPS certificates enabled
  for the tailnet (Tailscale Serve needs them).
- An app signed with a development (or ad hoc) provisioning profile that lists the phone.
- Python 3 (standard library only).

## Steps

1. **Check where the phone is.** `xcrun devicectl list devices`. If it shows `available` or
   `connected`, install directly instead (faster). If it is `unavailable`, use this route.
   `tailscale status` should list the phone as online.
2. **Build a device-signed app** from the working tree, as usual (`xcodebuild` for
   `generic/platform=iOS`, or an equivalent device build). Use the same scheme and configuration
   you would install directly. The result is `.../Build/Products/<Config>-iphoneos/<App>.app`.
3. **Get the phone's hardware UDID** so the script can check the profile includes it:
   ```bash
   xcrun devicectl list devices --json-output /tmp/devices.json
   # result.devices[].hardwareProperties.udid, matched on deviceProperties.name
   ```
   This works even while the phone is unavailable.
4. **Publish:**
   ```bash
   python3 scripts/ota_publish.py \
     --app /path/to/App.app --slug <app-slug> --title "<App Name>" \
     --port <port> --udid <UDID>
   ```
   It verifies the signature, the profile's expiry and that the UDID is listed; packages the IPA;
   writes the manifest and install page; starts a localhost-only file server if needed; adds the
   Tailscale Serve route if needed; then downloads the page, manifest and IPA over the tailnet URL
   and checks the IPA hash. It prints JSON with `install_page`.
5. **Send the user the `install_page` link**, and tell them: keep Tailscale connected on the phone,
   open the link in Safari, tap Install, and install over the existing app (do not delete it
   unless they want a fresh start; installing over it keeps its data).
6. **Report honestly.** A published, read-back link is not an installed app. Installation and
   launch are confirmed only when the user says so.

Re-running step 4 for a new build replaces `index.html` and keeps the three newest IPAs.

## Ports and paths

All routes share `https://<mac>.<tailnet>.ts.net:8443` (tailnet only). Pick an unused local port
per app and keep it stable, and record it here so later runs reuse it:

| Slug | Local port | App |
| --- | --- | --- |
| `/my-app-dev` | 8771 | Example app (`com.example.myapp.dev`) |

Files live in `~/ota-serve/<slug>/` (outside every repo). The server log is `server.log` there.
If the Mac restarts, the next publish restarts the server; the Serve route persists.

## What this route cannot do

- **No launch arguments.** Flags passed by Xcode or `devicectl` are absent. Features gated on them
  are off unless the app has another switch.
- **No StoreKit configuration file.** Purchases go to the real App Store sandbox for that bundle, so
  paywalls only load if that app's products exist in App Store Connect. Test paywalls that rely on
  a local StoreKit file by running from Xcode instead.
- **Device must be in the profile.** A new phone needs registering and the profile regenerating,
  which is a signing change: ask first.
- **Not for App Store or TestFlight.** This is development distribution to your own devices.

## Cleanup

Remove an app's route and stop its server when it is no longer needed:
```bash
tailscale serve --https=8443 --set-path=/<slug> off
lsof -nP -t -iTCP:<port> -sTCP:LISTEN | xargs kill
```
Delete `~/ota-serve/<slug>/` only when the builds are no longer needed for reinstalling.
