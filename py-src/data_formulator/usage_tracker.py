# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""Per-identity LLM token usage tracking.

Every request already resolves an :func:`data_formulator.auth.identity.
get_identity_id` value (``local:<user>``, ``user:<sub>``, or
``browser:<uuid>``) to scope workspaces, sessions and credentials. This
module reuses that same identity to answer a question none of those answer:
*how many tokens has each identity actually burned, on which model, and
what does that cost?*

Storage: ``DATA_FORMULATOR_HOME/usage.db`` (unencrypted — token counts and
model names aren't secrets, unlike the credential vault).

Pricing is deliberately NOT hard-coded here. Provider pricing changes and
guessing wrong would silently mis-bill a client. Instead ``pricing.json``
(also under DATA_FORMULATOR_HOME) is a plain, user-edited table of USD per
million tokens; any model missing from it reports token counts with
``estimated_cost_usd: null`` rather than a fabricated number. Ollama is
seeded at $0/$0 because self-hosted inference has no per-token provider
cost — that one fact isn't going to change.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_DEFAULT_PRICING = {
    # endpoint -> model -> {"input": $/1M input tokens, "output": $/1M output tokens}
    # Only Ollama is a hard fact (self-hosted, zero marginal cost). Every
    # other provider/model is left for the operator to fill in from the
    # provider's own pricing page — do not guess numbers here.
    "ollama": {"*": {"input": 0.0, "output": 0.0}},
}

_lock = threading.Lock()
_db_path: Optional[Path] = None
_pricing_path: Optional[Path] = None
_pricing_cache: Optional[dict] = None


def _home() -> Path:
    from data_formulator.datalake.workspace import get_data_formulator_home
    return get_data_formulator_home()


def _init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS usage (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                identity_id        TEXT NOT NULL,
                ts                 TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                endpoint           TEXT NOT NULL,
                model              TEXT NOT NULL,
                prompt_tokens      INTEGER NOT NULL DEFAULT 0,
                completion_tokens  INTEGER NOT NULL DEFAULT 0,
                total_tokens       INTEGER NOT NULL DEFAULT 0,
                estimated_cost_usd REAL
            )
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_identity ON usage(identity_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage(ts)")


def _load_pricing(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Failed to parse %s, using defaults", path)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(_DEFAULT_PRICING, indent=2) + "\n", encoding="utf-8"
        )
        logger.info(
            "Created %s — fill in $/1M-token input/output prices per "
            "endpoint+model to get real cost estimates (unpriced models "
            "still track token counts, just with estimated_cost_usd=null).",
            path,
        )
    return dict(_DEFAULT_PRICING)


def _ensure_init() -> None:
    global _db_path, _pricing_path, _pricing_cache
    if _db_path is not None:
        return
    with _lock:
        if _db_path is not None:
            return
        home = _home()
        _db_path = home / "usage.db"
        _pricing_path = home / "pricing.json"
        _init_db(_db_path)
        _pricing_cache = _load_pricing(_pricing_path)


def _price_for(endpoint: str, model: str) -> Optional[dict]:
    assert _pricing_cache is not None
    provider_table = _pricing_cache.get(endpoint, {})
    return provider_table.get(model) or provider_table.get("*")


def record_usage(
    identity_id: str,
    endpoint: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> None:
    """Log one LLM call's token usage. Never raises — a tracking failure
    must not break the actual LLM request it's piggybacking on."""
    try:
        _ensure_init()
        total = (prompt_tokens or 0) + (completion_tokens or 0)
        price = _price_for(endpoint, model)
        cost = None
        if price is not None:
            cost = (
                (prompt_tokens or 0) * price.get("input", 0.0)
                + (completion_tokens or 0) * price.get("output", 0.0)
            ) / 1_000_000
        with sqlite3.connect(_db_path) as conn:
            conn.execute(
                "INSERT INTO usage (identity_id, endpoint, model, prompt_tokens, "
                "completion_tokens, total_tokens, estimated_cost_usd) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (identity_id, endpoint, model, prompt_tokens or 0,
                 completion_tokens or 0, total, cost),
            )
    except Exception:
        logger.exception("Failed to record usage (identity=%s, model=%s)", identity_id, model)


def get_summary(identity_id: Optional[str] = None, since: Optional[str] = None) -> dict:
    """Aggregate usage. Scoped to one identity when given, otherwise all
    identities (caller is responsible for gating that to admins)."""
    _ensure_init()
    where = []
    params: list = []
    if identity_id is not None:
        where.append("identity_id = ?")
        params.append(identity_id)
    if since is not None:
        where.append("ts >= ?")
        params.append(since)
    clause = f"WHERE {' AND '.join(where)}" if where else ""

    with sqlite3.connect(_db_path) as conn:
        conn.row_factory = sqlite3.Row
        by_identity = conn.execute(f"""
            SELECT identity_id,
                   SUM(prompt_tokens) AS prompt_tokens,
                   SUM(completion_tokens) AS completion_tokens,
                   SUM(total_tokens) AS total_tokens,
                   SUM(estimated_cost_usd) AS estimated_cost_usd,
                   COUNT(*) AS calls
            FROM usage {clause}
            GROUP BY identity_id
            ORDER BY total_tokens DESC
        """, params).fetchall()

        by_model = conn.execute(f"""
            SELECT endpoint, model,
                   SUM(prompt_tokens) AS prompt_tokens,
                   SUM(completion_tokens) AS completion_tokens,
                   SUM(total_tokens) AS total_tokens,
                   SUM(estimated_cost_usd) AS estimated_cost_usd,
                   COUNT(*) AS calls
            FROM usage {clause}
            GROUP BY endpoint, model
            ORDER BY total_tokens DESC
        """, params).fetchall()

    return {
        "by_identity": [dict(r) for r in by_identity],
        "by_model": [dict(r) for r in by_model],
    }
