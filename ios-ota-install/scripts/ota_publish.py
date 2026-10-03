#!/usr/bin/env python3
"""Publish a signed iOS .app as a Safari over-the-air install link on your tailnet.

The link only works on devices signed into the tailnet and listed in the app's provisioning
profile. Nothing is uploaded to Apple, TestFlight or the public internet.

Steps: check the signing profile, package an IPA, write an install manifest and page, make sure
a local static server and the Tailscale Serve route are up, then read everything back over the
tailnet URL and compare the IPA hash.
"""
import argparse
import datetime
import hashlib
import html
import json
import os
import plistlib
import shutil
import socket
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

HTTPS_PORT = 8443
SERVER_SCRIPT = Path(__file__).with_name("ota_static_server.py")


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    sys.exit(1)


def run(cmd, **kwargs):
    return subprocess.run(cmd, check=True, capture_output=True, text=True, **kwargs).stdout


def read_profile(app):
    profile = app / "embedded.mobileprovision"
    if not profile.exists():
        fail(f"{app} has no embedded.mobileprovision; build it signed for a device first")
    decoded = subprocess.run(["security", "cms", "-D", "-i", str(profile)], check=True, capture_output=True).stdout
    return plistlib.loads(decoded)


def tailnet_host():
    status = json.loads(run(["tailscale", "status", "--json"]))
    name = status.get("Self", {}).get("DNSName", "").rstrip(".")
    if not name:
        fail("this Mac has no Tailscale DNS name; is Tailscale running and logged in?")
    return name


def port_open(port):
    with socket.socket() as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def ensure_server(root, port):
    if port_open(port):
        return "already running"
    log = root / "server.log"
    subprocess.Popen(
        [sys.executable, str(SERVER_SCRIPT), "--root", str(root), "--port", str(port)],
        stdout=open(log, "a"), stderr=subprocess.STDOUT, start_new_session=True,
    )
    for _ in range(20):
        if port_open(port):
            return f"started (log: {log})"
        time.sleep(0.25)
    fail(f"the static server did not start on 127.0.0.1:{port}; see {log}")


def ensure_serve_route(slug, port):
    target = f"http://127.0.0.1:{port}"
    status = subprocess.run(["tailscale", "serve", "status", "--json"], capture_output=True, text=True).stdout
    if f"/{slug}" in status and target in status:
        return "already routed"
    run(["tailscale", "serve", "--bg", f"--https={HTTPS_PORT}", f"--set-path=/{slug}", target])
    return "route added"


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.status, response.headers.get("Content-Type", ""), response.read()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--app", required=True, type=Path, help="Device-signed .app bundle")
    parser.add_argument("--slug", required=True, help="URL path, e.g. my-app-dev")
    parser.add_argument("--title", help="Name shown in the install prompt (default: the app's display name)")
    parser.add_argument("--port", type=int, required=True, help="Local port for this app's static server")
    parser.add_argument("--udid", action="append", default=[], help="Device UDID that must be in the profile (repeatable)")
    parser.add_argument("--root", type=Path, default=Path.home() / "ota-serve", help="Where served files live")
    parser.add_argument("--keep", type=int, default=3, help="How many older IPAs to keep")
    args = parser.parse_args()

    app = args.app.resolve()
    if not (app / "Info.plist").exists():
        fail(f"{app} is not an app bundle")
    info = plistlib.load(open(app / "Info.plist", "rb"))
    bundle_id = info["CFBundleIdentifier"]
    version = info.get("CFBundleShortVersionString", "0")
    build = info.get("CFBundleVersion", "0")
    title = args.title or info.get("CFBundleDisplayName") or info.get("CFBundleName") or bundle_id

    profile = read_profile(app)
    devices = profile.get("ProvisionedDevices", [])
    expires = profile.get("ExpirationDate")
    if profile.get("ProvisionsAllDevices"):
        fail("enterprise profiles are not used here")
    for udid in args.udid:
        if udid not in devices:
            fail(f"device {udid} is not in profile '{profile.get('Name')}'; register it and rebuild")
    if expires and expires < datetime.datetime.now(expires.tzinfo):
        fail(f"profile '{profile.get('Name')}' expired on {expires}")
    verify = subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], capture_output=True, text=True)
    if verify.returncode != 0:
        fail(f"code signature does not verify: {verify.stderr.strip()}")

    site = args.root / args.slug
    site.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    ipa_name = f"{args.slug}-{version}-{build}-{stamp}.ipa"
    ipa = site / ipa_name
    with zipfile.ZipFile(ipa, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in app.rglob("*"):
            arcname = Path("Payload") / app.name / path.relative_to(app)
            if path.is_symlink():
                info_entry = zipfile.ZipInfo(str(arcname))
                info_entry.create_system = 3
                info_entry.external_attr = 0o120777 << 16
                archive.writestr(info_entry, os.readlink(path))
            elif path.is_file():
                archive.write(path, arcname)
    digest = hashlib.sha256(ipa.read_bytes()).hexdigest()

    host = tailnet_host()
    base = f"https://{host}:{HTTPS_PORT}/{args.slug}"
    manifest_name = f"manifest-{stamp}.plist"
    manifest = {"items": [{
        "assets": [{"kind": "software-package", "url": f"{base}/{ipa_name}"}],
        "metadata": {"bundle-identifier": bundle_id, "bundle-version": version, "kind": "software", "title": title},
    }]}
    (site / manifest_name).write_bytes(plistlib.dumps(manifest))
    install = "itms-services://?action=download-manifest&url=" + urllib.parse.quote(f"{base}/{manifest_name}", safe="")
    page = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{html.escape(title)}</title>
<style>body{{font:17px -apple-system,sans-serif;margin:32px;background:#120d1f;color:#f4eefc}}
a.button{{display:block;padding:18px;border-radius:14px;background:#8b5cf6;color:#fff;text-align:center;
text-decoration:none;font-weight:600;margin:24px 0}}small{{color:#b9add0}}</style></head><body>
<h1>{html.escape(title)}</h1><p>Version {html.escape(version)} ({html.escape(build)})<br>
<small>Published {stamp}. Keep Tailscale connected. Installing over the existing app keeps its data.</small></p>
<a class="button" href="{html.escape(install)}">Install {html.escape(title)} {html.escape(build)}</a>
<p><small>SHA-256 {digest}</small></p></body></html>"""
    (site / "index.html").write_text(page)

    # Keep the newest IPAs and manifests only.
    for pattern in ("*.ipa", "manifest-*.plist"):
        files = sorted(site.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in files[args.keep:]:
            old.unlink()

    server_state = ensure_server(site, args.port)
    route_state = ensure_serve_route(args.slug, args.port)

    # Read back over the tailnet URL, as the phone will.
    page_status, page_type, page_body = fetch(f"{base}/")
    manifest_status, manifest_type, manifest_body = fetch(f"{base}/{manifest_name}")
    ipa_status, _, ipa_body = fetch(f"{base}/{ipa_name}")
    served_digest = hashlib.sha256(ipa_body).hexdigest()
    if served_digest != digest:
        fail("the served IPA does not match the packaged one")
    if plistlib.loads(manifest_body)["items"][0]["metadata"]["bundle-identifier"] != bundle_id:
        fail("the served manifest names a different app")

    print(json.dumps({
        "install_page": f"{base}/",
        "app": title, "bundle_id": bundle_id, "version": version, "build": build,
        "profile": profile.get("Name"), "profile_expires": str(expires), "profile_devices": len(devices),
        "ipa": str(ipa), "sha256": digest, "ipa_megabytes": round(len(ipa_body) / 1_048_576, 1),
        "server": server_state, "serve_route": route_state,
        "readback": {"page": page_status, "manifest": f"{manifest_status} {manifest_type}", "ipa": ipa_status},
    }, indent=2))


if __name__ == "__main__":
    main()
