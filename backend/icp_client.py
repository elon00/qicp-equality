"""Internet Computer (ICP) Boundary Node Client for QICP Protocol.

Executes queries directly against live DFINITY boundary nodes (https://ic0.app
and https://icp-api.io) using authentic CBOR serialization and HTTP v2 API.
"""
import cbor2
import hashlib
import httpx
from typing import Any, Dict, Optional, Tuple


class ICPBoundaryClient:
    """Client for querying live Internet Computer mainnet boundary nodes."""

    BOUNDARY_NODES = [
        "https://ic0.app",
        "https://icp-api.io",
    ]

    def __init__(self, primary_url: Optional[str] = None):
        self.primary_url = primary_url or self.BOUNDARY_NODES[0]

    async def check_boundary_node_health(self) -> Dict[str, Any]:
        """Check status and reachability of live ICP boundary nodes."""
        results = {}
        async with httpx.AsyncClient(timeout=6.0) as client:
            for url in self.BOUNDARY_NODES:
                try:
                    resp = await client.get(f"{url}/api/v2/status")
                    results[url] = {
                        "reachable": resp.status_code == 200,
                        "status_code": resp.status_code,
                        "cbor_content_type": "application/cbor" in resp.headers.get("content-type", ""),
                    }
                except Exception as e:
                    results[url] = {
                        "reachable": False,
                        "error": str(e),
                    }
        return results

    async def query_canister_raw(
        self,
        canister_id: str,
        method_name: str,
        arg_bytes: bytes = b"",
    ) -> Tuple[bool, Any]:
        """Send a read-only query call to an on-chain canister via boundary node."""
        envelope = {
            "content": {
                "request_type": "query",
                "canister_id": canister_id.encode("utf-8"),
                "method_name": method_name,
                "arg": arg_bytes,
                "sender": b"\x04", # Anonymous principal representation
            }
        }
        cbor_body = cbor2.dumps(envelope)
        url = f"{self.primary_url}/api/v2/canister/{canister_id}/query"

        async with httpx.AsyncClient(timeout=8.0) as client:
            try:
                resp = await client.post(
                    url,
                    content=cbor_body,
                    headers={"Content-Type": "application/cbor"},
                )
                if resp.status_code == 200:
                    decoded = cbor2.loads(resp.content)
                    return True, decoded
                else:
                    return False, f"HTTP Error {resp.status_code}: {resp.text}"
            except Exception as e:
                return False, f"Boundary node query failed: {e}"
