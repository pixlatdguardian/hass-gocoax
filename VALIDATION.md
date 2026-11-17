# Read-only fork validation

Validated November 17, 2026. Upstream base:
`d477493fe9c82afd2ca28ef0f5264c6d1c251e9c`.

## Physical adapters

The actual bundled async client was exercised against two MA2500D adapters.
Firmware image version **2.0.16.0** was supplied by the operator; the observed
SoC SDK version was **1.18.15**. These are separate version identifiers.

Each adapter completed setup and two consecutive polls, with **31 allowlisted
requests per device**. The test verified:

- Stable local MAC identity between setup and polling.
- Local/controller node identities and reciprocal peer MAC association.
- One peer per adapter, MoCA link up and five bonded channels.
- Ethernet link up at 2500 Mbps and directional PHY readings around 3.4 Gbps.
- Increasing/non-decreasing packet counters between polls.
- Configured band and boolean encryption-mode flag reads.
- Per-request target/method allowlist checks through aiohttp tracing.

All requests were observational getters, including firmware POST getters. No
configuration setters, restart, restore, firmware upload, shell, password/key
getter or write endpoint was called. Local captures and live-test outputs are
git-ignored and excluded from the release archive. Published fixtures replace
MACs/counters and omit unused response fields and FMR headers/tails.

## Automated checks

- **34 portable client/protocol tests** using Python 3.12 and aiohttp 3.14.5.
  They include an actual loopback HTTP server, cookie/CSRF handling, session
  reuse/refresh, bounded retries, authentication errors, invalid JSON, response
  limits, denied redirects/write/key operations, captured numeric decoding,
  unsigned counters, sparse node masks and missing optional data.
- **23 HA integration tests**, using an isolated Linux Python 3.14 environment:
  Home Assistant **2026.10.4**, pytest-homeassistant-custom-component **0.13.375**,
  pytest **9.0.3**, aiohttp **3.14.5**. They cover config flows, real integration
  setup/unload, session cleanup, coordinator errors, diagnostics, real entity IDs
  and peer discovery/reordering/departure. Device transport is mocked in HA tests.
- Ruff lint and formatting checks; Python syntax and Git whitespace checks.
- GitHub Actions defines separate client and HA regression jobs. See the fork's
  Actions page for the run corresponding to the commit being reviewed.

The HA test harness currently pins the October 2026 core. This document does not
claim runtime testing on every HA/firmware version. The production HA instance
was not contacted, modified, reloaded or restarted.

## Remaining limits

Only two physical MA2500D adapters were tested; mixed-version and sixteen-node
networks are not hardware-validated. Sparse masks and missing data have synthetic
regression coverage. SNR/power, exact model identification, and firmware image
metadata remain unknown where no verified safe source exists. Band/encryption
entities describe configured flags, not an independent cryptographic audit.

The hardware's HTTP transport remains unencrypted. The component cannot add TLS
to an HTTP-only adapter. Future HA deployment and UI verification are separate
from this build; no production rollout has been performed.
