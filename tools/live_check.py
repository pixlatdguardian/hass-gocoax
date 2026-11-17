"""Exercise the fork's actual monitoring client, without touching Home Assistant."""

import argparse
import asyncio
import ipaddress
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import aiohttp

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components" / "gocoax"))
from pygocoax import GoCoaxClient  # noqa: E402
from pygocoax.client import READ_OPERATIONS, READ_PAGES  # noqa: E402


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", action="append", required=True)
    args = parser.parse_args()
    if len(set(args.host)) != 2 or not all(
        ipaddress.ip_address(host).is_private for host in args.host
    ):
        raise ValueError("Supply two distinct private adapter IP addresses")
    username = os.environ.pop("GOCOAX_USERNAME", "")
    password = os.environ.pop("GOCOAX_PASSWORD", "")
    if not username or not password or password.startswith("op://"):
        raise RuntimeError("Use op run with the approved credential references")
    output, identities, snapshots = [], {}, {}
    allowed = {spec[0] for spec in READ_OPERATIONS.values()}
    for host in args.host:
        calls = []

        async def check_request(_session, _context, params, calls=calls, host=host):
            path = params.url.path
            assert params.url.host == host
            assert (params.method == "GET" and path in READ_PAGES) or (
                params.method == "POST" and path in allowed
            )
            calls.append({"method": params.method, "path": path})

        trace = aiohttp.TraceConfig()
        trace.on_request_start.append(check_request)
        async with (
            aiohttp.ClientSession(
                cookie_jar=aiohttp.DummyCookieJar(),
                trace_configs=[trace],
                trust_env=False,
            ) as session,
            GoCoaxClient(host, username, password, session=session) as client,
        ):
            identities[host] = await client.get_mac_address()
            first = await client.get_status()
            await asyncio.sleep(1)
            second = await client.get_status()
            assert first.mac_address == second.mac_address == identities[host]
            assert second.link_status and second.peer_count == 1
            assert second.ethernet_link and second.ethernet_speed == 2500
            assert second.channel_count == 5
            assert second.frequency_band is not None
            assert isinstance(second.encryption_enabled, bool)
            assert len(second.phy_rates) == 1
            assert all(r.tx_rate and r.rx_rate for r in second.phy_rates)
            assert second.packets.tx.ok >= first.packets.tx.ok
            assert second.packets.rx.ok >= first.packets.rx.ok
            snapshots[host] = second
            output.append(
                {
                    "host": host,
                    "node": second.node_id,
                    "controller": second.nc_node_id,
                    "link_up": second.link_status,
                    "peer_count": second.peer_count,
                    "ethernet_mbps": second.ethernet_speed,
                    "channels": second.channel_count,
                    "frequency_mhz": second.lof,
                    "soc_sdk": second.soc_version,
                    "configured_bands": second.frequency_band,
                    "encryption_enabled": second.encryption_enabled,
                    "phy": [
                        {"tx_mbps": r.tx_rate, "rx_mbps": r.rx_rate}
                        for r in second.phy_rates
                    ],
                    "request_count": len(calls),
                    "requests": calls,
                }
            )
            print(
                f"{host}: setup + two polls passed; peer={second.peer_count}, Ethernet={second.ethernet_speed} Mbps, PHY TX/RX={second.phy_rates[0].tx_rate}/{second.phy_rates[0].rx_rate} Mbps",
                flush=True,
            )
    a, b = snapshots.values()
    assert a.network_peers[0].mac_address == b.mac_address
    assert b.network_peers[0].mac_address == a.mac_address
    assert a.nc_node_id == b.nc_node_id
    destination = ROOT / "live-results" / "latest.json"
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "time": datetime.now(UTC).isoformat(),
                "passed": True,
                "cross_device_peer_identity_verified": True,
                "devices": output,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        "Both devices passed reciprocal-peer and controller checks. HA was not accessed."
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as error:
        # No traceback, response, auth object, cookies or credentials in terminal output.
        print(
            f"Live validation failed ({type(error).__name__}); no response details printed."
        )
        raise SystemExit(1) from None
