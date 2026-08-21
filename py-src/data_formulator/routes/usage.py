# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""REST API for per-identity LLM token usage / cost reporting.

``/summary`` is self-service: any authenticated identity can see their own
usage, the same trust boundary as ``/api/credentials/list``.

``/all`` aggregates across every identity on this server — meaningful once
real auth (not just single-user local mode) is turned on and multiple
clients share a deployment. Gated by ``USAGE_ADMIN_IDENTITIES`` (comma
separated list of identity ids, e.g. ``user:sidney@example.com``) so it
isn't wide open by default; single-user local mode is allowed through
automatically since there's only ever one possible identity to see anyway.
"""
from __future__ import annotations

import logging
import os

from flask import Blueprint, request

from data_formulator import usage_tracker
from data_formulator.auth.identity import get_identity_id, is_local_mode
from data_formulator.error_handler import json_ok
from data_formulator.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)

usage_bp = Blueprint("usage", __name__, url_prefix="/api/usage")


@usage_bp.route("/summary", methods=["GET"])
def summary():
    """Usage totals for the current identity only."""
    identity = get_identity_id()
    since = request.args.get("since")
    return json_ok(usage_tracker.get_summary(identity_id=identity, since=since))


@usage_bp.route("/all", methods=["GET"])
def all_usage():
    """Usage totals across every identity. Admin-gated (see module docstring)."""
    identity = get_identity_id()
    admins = {
        a.strip() for a in os.environ.get("USAGE_ADMIN_IDENTITIES", "").split(",") if a.strip()
    }
    if not is_local_mode() and identity not in admins:
        raise AppError(ErrorCode.ACCESS_DENIED, "Not authorized to view platform-wide usage")

    since = request.args.get("since")
    return json_ok(usage_tracker.get_summary(since=since))
