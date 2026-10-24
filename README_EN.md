# AdBlock ESP32

[🇻🇳 Tiếng Việt](README.md) | [🇬🇧 English](README_EN.md) | [🇯🇵 日本語](README_JP.md)

A **Pi-hole-style DNS ad-blocker** that runs on a **$2 ESP32-C3** — *no external PSRAM required*.

> 📰 Featured on [Tom's Hardware](https://www.tomshardware.com/networking/clever-hacker-fits-537-000-domains-in-a-tiny-usd5-esp32-ad-blocking-dongle-firmware-uses-only-around-50kb-of-ram-and-can-answer-blocked-lookups-in-10-milliseconds), [XDA Developers](https://www.xda-developers.com/this-tiny-esp32-powered-gadget-blocks-537000-domains-only-uses-50kb-of-ram/), and [Korben](https://korben.info/en/half-million-ad-blocking-domains-50kb-ram-esp32.html).

The trick everyone misses: you don't need to keep the blocklist in RAM. Store the
domains as **sorted 40-bit hashes in flash** and binary-search them. 140,000+ to 250,000+ domains
fit in ~0.7–1.3 MB of flash and are matched in ~10 ms, using **~50–80 KB of RAM**.

```
query in ──▶ extract domain ──▶ FNV-1a hash (+ parent suffixes)
         ──▶ 4096-entry RAM index binary search
         ──▶ read single flash hash bucket
              ├─ hit  ──▶ answer 0.0.0.0   (sinkholed)
              └─ miss ──▶ forward to upstream resolver, relay reply
```

---

## Key Features

- 🛡️ **Network-wide DNS Blocking**: Blocks ads, trackers, telemetry, and malicious domains for all devices on your local network (phones, Smart TVs, PCs, tablets).
- 🌐 **Modern Bilingual Web Dashboard**: English (EN) and Vietnamese (VI) language toggle, sticky responsive navigation bar with ScrollSpy, mobile-friendly design.
- ⚡ **Real-time DNS Query Log**: Inspect the last 16 DNS queries processed in RAM (domain, client IP, blocked/allowed verdict, age).
- 👥 **Client Management & IP Banning**: Monitor DNS query statistics per IP, with one-click device banning/unbanning.
- 📶 **Wi-Fi Scanner**: Scan nearby wireless networks directly from the web UI without interrupting saved Wi-Fi configuration.
- 🔄 **Over-The-Air (OTA) Updates**: Update both firmware and blocklist over Wi-Fi without needing a USB cable, plus automated remote blocklist sync.
- 🇻🇳 **Vietnam Whitelist Optimized**: Integrated whitelist (`whitelist.txt`) covering Vietnamese e-government (VNeID, Public Services), major banking apps, e-wallets, and news portals to eliminate false positives.
- 🔒 **Security Hardened**: HTTP Basic Authentication on state-changing endpoints, CSRF mitigation via `X-Requested-With`, and HTML escaping against stored XSS.

---

## Why this is interesting

Most ESP32 DNS sinkholes load the blocklist (domain *strings*) into RAM, so they
demand PSRAM. This project stores fixed **5-byte (40-bit) hashes in flash** instead:

| Feature | String-in-RAM approach | This (Hash-in-Flash + RAM Index) |
|---|---|---|
| **Hardware** | ESP32 + PSRAM (~$8) | ESP32-C3, no PSRAM (~$2) |
| **Capacity** | ~20k–40k domains without PSRAM | **140,000 to 250,000+ domains in 4MB flash** |
| **RAM Usage** | Nearly all available heap | **~50–80 KB** |
| **Lookup Latency** | String search | ~1–2 flash reads (~10 ms total incl. WiFi RTT) |
| **Collisions** | 0 | 0 at 141k (~1 at 537k) |

**Why 40 bits?** It's the sweet spot for flash storage. Collisions follow the
birthday bound — at 141k domains you get ~0 collisions, at 537k about 1 (i.e. one domain
gets over-blocked). Dropping to 32 bits would save 20% flash but cost ~7 collisions at 250k;
going to 64 bits wastes 3 bytes per domain.

---

## Hardware

- Any **ESP32-C3** board (tested on a **C3 SuperMini**), 4 MB flash, **no PSRAM needed**.
- Classic **ESP32** (DevKit / WROOM, 4 MB) is also supported: `pio run -e esp32dev -t upload`.
- Power via a **stable USB source** (phone charger or router USB port).
- A **USB-A → USB-C adapter** allows plugging directly into the back of your home router.

### 3D Printable Case

A snap-fit printable enclosure for the C3 SuperMini: [`hardware/esp32-c3-supermini-enclosure.stl`](hardware/esp32-c3-supermini-enclosure.stl).
- No supports required; 0.2 mm layer height, ~15% infill.
- Keep the antenna trace clear (on the short edge opposite the USB-C port).

---

## Build & Flash (PlatformIO)

Initial flash requires a USB cable. After that, all updates (firmware and blocklist) happen over Wi-Fi.

```bash
# 1. Copy secrets template and edit credentials
cp src/secrets.example.h src/secrets.h
# Edit src/secrets.h:
# - WIFI_SSID / WIFI_PASS (optional: leave blank to use the captive portal)
# - WEB_USER / WEB_PASS / OTA_PASS (set secure admin passwords)

# 2. Build blocklist binary hash table
python tools/build_blocklist.py data/blocklist.bin

# 3. Flash firmware and blocklist filesystem (one-time USB flash)
pio run -t upload
pio run -t uploadfs

# 4. Monitor serial boot output
pio device monitor          # -> http://c3adblock.local
```

### Initial Wi-Fi Setup (Captive Portal)

If Wi-Fi credentials are not preset in `secrets.h`, the device starts an open access point named:
`C3-AdBlock-XXXX` (where XXXX is the board's MAC suffix).
1. Connect to this Wi-Fi network from your phone or PC.
2. The setup portal opens automatically.
3. Select your home Wi-Fi network, type the password, and save.
4. The device reboots and connects to your local network.

---

## Web Dashboard & Management

Open your browser and navigate to:
**`http://c3adblock.local`** (or the IP address assigned by your router).

- **Admin Sign In**: Clean authentication screen with credentials remembrance and password toggle, plus optional quick read-only stats access.
- **Menu Navigation**: Smoothly jump to Overview, DNS Queries, Devices, Filters, Wi-Fi Network, and Maintenance sections.
- **Language Switch**: Click the **VI / EN** toggle in the menu bar to switch UI languages instantly.
- **Pause / Resume**: Temporarily pause ad-blocking (30s, 5m, 30m, or until manually resumed).
- **Recent Queries**: Live table of the 16 most recent DNS lookups with domain, client IP, blocked/allowed badge, and timestamp.
- **Per-Device Statistics**: See query count per client and ban/unban rogue devices.
- **Custom Filters**: Add local blacklist rules directly from the web interface.
- **Wi-Fi Scanner**: Scan surrounding 2.4GHz Wi-Fi networks with RSSI signal meters.
- **Over-The-Air (OTA) Updates**:
  - **Blocklist**: Upload new `blocklist.bin` files or configure remote auto-updates from a URL.
  - **Firmware**: Upload `.pio/build/c3/firmware.bin` directly via the browser.

---

## Configuring Your Devices / Router

To protect your whole home network, set the ESP32-C3's IP address as your **Primary DNS Server** in your router's DHCP settings.

To test manually on a client:
```bash
dig @<c3-ip> doubleclick.net   # -> 0.0.0.0  (blocked)
dig @<c3-ip> github.com        # -> real IP  (forwarded)
```

---

## Security Architecture

- **Authentication**: All state-changing endpoints (`/ban`, `/addblock`, `/upload`, `/update`, `/setupdate`, `/forgetwifi`) require HTTP Basic Auth (`WEB_USER`/`WEB_PASS`).
- **CSRF Mitigation**: Mutating requests require custom header `X-Requested-With: c3-adblock` which browser cross-origin requests cannot forge.
- **XSS Prevention**: Custom domain entries and Wi-Fi SSIDs are strictly HTML-escaped.
- **Dual-OTA Flash Layout**: Dual app partitions allow safe rollback if an OTA update fails.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.
