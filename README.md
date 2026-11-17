# goCoax MoCA — read-only Home Assistant integration

A monitoring fork of [homeassistant-projects/hass-gocoax](https://github.com/homeassistant-projects/hass-gocoax), originally by Ryan Snodgrass. Apache 2.0 license and original attribution are retained in [LICENSE.md](LICENSE.md).

Version **1.2.0** targets the **MA2500D firmware 2.0.16.0** protocol. The client
has been exercised against two physical adapters. Other models/firmware require
validation; upstream's former compatibility list is not a claim about this fork.

## What it reads

- MoCA link/controller state, local node ID and discovered peers, including node 0.
- Local MAC/IP, network MoCA version and Ethernet packet/error/drop counters.
- Directional peer PHY rates decoded from the firmware's packed FMR data.
- Ethernet link, speed and duplex; SoC SDK version.
- Configured frequency bands, lowest operating frequency, beacon/primary/
  secondary/first channels and bonded channel count.
- Configured legacy/enhanced MoCA encryption flags, without requesting any keys.

The SoC SDK version is kept separate from the firmware image version. Unknown
image/model/SNR/power fields remain unknown. Optional unavailable PHY data does
not become a misleading zero; unavailable peers keep their existing entities.

## Device access policy

There are no configuration controls, setters, reboot, restore, upgrade, firmware
uploads or shell operations. Adapter requests are limited to fixed status pages
and reviewed getter endpoints with validated numeric payloads. Firmware getters
use HTTP POST even when the endpoint name ends in `/GET`. All redirects are
refused, and owned sessions ignore environment proxies.

The MA2500D management interface uses HTTP Basic authentication over unencrypted
HTTP. Use a unique adapter password and a trusted management network. This fork
does not add HTTPS support to the hardware. Authentication/session cookies and
CSRF tokens stay in memory; raw responses are not logged. Diagnostic exports
redact credentials, MAC fields, host/IP and the host-bearing entry title.

Normal observational queries still create sessions, consume resources and may
appear in device logs. A read-only policy means no configuration commands are
sent; it is not a promise of zero transient device activity.

## Home Assistant configuration

The integration retains the `gocoax` domain and existing entity unique-ID formats.
Configure an adapter address and credentials through Settings → Devices & Services.
Polling can be set from 10–300 seconds, default 30. Timeout/connection failures
mark entities unavailable rather than silently presenting stale data as fresh.

The fork is a replacement for the upstream component, not a second integration
to install alongside it. Back up HA before a future deployment and replace the
existing `custom_components/gocoax` component as one unit. HACS users should
select this repository as their custom integration source rather than mixing
files from two repositories. The validation/build tooling does not deploy to HA.

1Password is used only by the optional development probe. HA uses its normal
config-entry credentials and does not require the 1Password CLI.

## Development and validation

```sh
python -m venv .venv
# Activate the virtualenv using your platform's normal command.
python -m pip install aiohttp pytest pytest-asyncio ruff
python -m pytest tests_client -q
python -m ruff check custom_components tests_client tools
```

`tests_client` covers anonymized captured layouts, sparse node masks, unsigned
64-bit counters, HTTP cookie/CSRF behavior, bounded retries, redirects, response
limits and denied write-shaped requests. `tests` exercises HA configuration,
coordinator lifecycle, diagnostics and real entity behavior using the HA test
harness. See [VALIDATION.md](VALIDATION.md) for measured results and limits.

For an explicitly authorized live test, supply the two target IPs and provide
`GOCOAX_USERNAME` / `GOCOAX_PASSWORD` only through a secret manager or process
environment. `tools/live_check.py --host <adapter-a> --host <adapter-b>` performs
setup and two polls against each, checks reciprocal peer identities, and writes
a local git-ignored result. Never commit credential references, local captures,
session cookies, real device identifiers or unredacted diagnostic bundles.

The live validator currently asserts the tested two-node MA2500D setup: one peer,
five channels and 2.5 GbE on each adapter. The integration itself supports the
firmware's sixteen-node mask and dynamically adds sensors for new peers.
