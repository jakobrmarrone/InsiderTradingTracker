import math
import pandas as pd

# -------- utilities --------
def _get_path(obj, path, default=None):
    """Safe dotted-path getter (e.g., 'amounts.shares')."""
    cur = obj
    for part in path.split("."):
        if cur is None:
            return default
        if isinstance(cur, dict):
            cur = cur.get(part, default)
        elif isinstance(cur, list):
            try:
                idx = int(part)
                cur = cur[idx]
            except (ValueError, IndexError, TypeError):
                # Not an index or out of range
                return default
        else:
            return default
    return cur if cur is not None else default

def _first(obj, *paths, default=None):
    """Return the first non-None value among candidate paths."""
    for p in paths:
        v = _get_path(obj, p, None)
        if v is not None:
            return v
    return default

def _to_num(x):
    try:
        return float(x)
    except Exception:
        return math.nan

def _direction(code, acq_disp, table, is_holding=False):
    if is_holding:
        return "HOLDING"
    c = (code or "").upper()
    a = (acq_disp or "").upper()
    if c == "P" or a == "A": return "BUYish"
    if c == "S" or a == "D": return "SELLish"
    if c == "F":             return "TaxWithhold"
    if c == "M":             return "Option/RSU"
    # Other SEC codes: G (gift), I (intra-fund), C (conversion), etc.
    # For derivative tables, unknown codes are often vest/settle
    return c or a or (table or "Other")

def _stake_change(shares, post_shares):
    s = _to_num(shares) or 0.0
    p = _to_num(post_shares) or 0.0
    return (s / (s + p)) if (s + p) > 0 else 0.0

# Map title to coarse role score
_ROLE_MAP = {
    "chief executive officer": 1.00, "ceo": 1.00, "president": 0.90, "chair": 0.90,
    "chief financial officer": 0.85, "cfo": 0.85, "chief operating officer": 0.80, "coo": 0.80,
    "general counsel": 0.75, "principal accounting officer": 0.75,
    "senior vice president": 0.70, "svp": 0.70, "vice president": 0.60, "vp": 0.60,
    "director": 0.60, "ten percent owner": 0.70
}
def _role_score(rel):
    rel = rel or {}
    title = (rel.get("officerTitle") or "").lower()
    for k, s in _ROLE_MAP.items():
        if k in title:
            return s
    if rel.get("isOfficer"):         return 0.50
    if rel.get("isTenPercentOwner"): return 0.70
    if rel.get("isDirector"):        return 0.60
    return 0.30

def _owners_iter(filing):
    """
    Yield (owner_dict, relationship_dict) for singular or plural owners.
    Most filings have a single 'reportingOwner', but support 'reportingOwners':[] too.
    """
    if isinstance(filing.get("reportingOwners"), list):
        for ow in filing["reportingOwners"]:
            yield ow, (ow.get("relationship") or {})
    else:
        ow = filing.get("reportingOwner") or {}
        yield ow, (ow.get("relationship") or {})

# -------- main flattener --------
def flatten_insider_payload(payload, debug: bool=False) -> pd.DataFrame:
    """
    Robust flattener for sec-api insider ownership/trading API.
    - Accepts dict with 'transactions' or a list of filings.
    - Emits one row per transaction leg (non-derivative or derivative).
    - Also emits rows for 'holdings' (Form 3/5) with direction='HOLDING'.
    """
    # Normalize top-level
    if isinstance(payload, dict):
        filings = payload.get("transactions", [])
    elif isinstance(payload, list):
        filings = payload
    else:
        filings = []

    rows = []
    if debug:
        print(f"[debug] filings: {len(filings)}")

    for i, filing in enumerate(filings, start=1):
        issuer = filing.get("issuer") or {}
        base_filing = {
            "id":              filing.get("id"),
            "accessionNo":     filing.get("accessionNo"),
            "schemaVersion":   filing.get("schemaVersion"),
            "documentType":    filing.get("documentType"),
            "filedAt":         filing.get("filedAt"),
            "periodOfReport":  filing.get("periodOfReport"),
            "issuer_cik":      issuer.get("cik"),
            "issuer_name":     issuer.get("name"),
            "issuer_symbol":   issuer.get("tradingSymbol"),
        }

        # Loop each (possibly multiple) owner; produce one row per owner per leg
        for owner, rel in _owners_iter(filing):
            base_owner = {
                "owner_cik":   owner.get("cik"),
                "owner_name":  owner.get("name"),
                "owner_title": rel.get("officerTitle"),
                "isDirector":  rel.get("isDirector"),
                "isOfficer":   rel.get("isOfficer"),
                "isTenPercentOwner": rel.get("isTenPercentOwner"),
                "role_score":  _role_score(rel),
            }
            base = {**base_filing, **base_owner}

            # --- Non-derivative TRANSACTIONS ---
            nd = (filing.get("nonDerivativeTable") or {})
            for leg in (nd.get("transactions") or []):
                # Flexible getters for common variants
                code     = _first(leg, "coding.code", "transactionCode.code", "transactionCoding.transactionCode")
                acq_disp = _first(leg, "amounts.acquiredDisposedCode", "transactionAcquiredDisposedCode")
                shares   = _first(leg, "amounts.shares")
                price    = _first(leg, "amounts.pricePerShare")
                post     = _first(leg, "postTransactionAmounts.sharesOwnedFollowingTransaction",
                                      "postTransactionAmounts.sharesOwnedFollowing")

                rows.append({
                    **base,
                    "table":            "nonDeriv",
                    "securityTitle":    _first(leg, "securityTitle", default=None),
                    "transactionDate":  _first(leg, "transactionDate", default=None),
                    "code":             code,
                    "acq_disp":         acq_disp,
                    "shares":           _to_num(shares),
                    "pricePerShare":    _to_num(price),
                    "post_shares":      _to_num(post),
                    "directOrIndirect": _first(leg, "ownershipNature.directOrIndirectOwnership", default=None),
                    "underlying_title": None,
                    "underlying_shares": None,
                    "direction":        _direction(code, acq_disp, "nonDeriv", is_holding=False),
                })

            # --- Derivative TRANSACTIONS ---
            for leg in ( (filing.get("derivativeTable") or {}).get("transactions") or [] ):
                code     = _first(leg, "coding.code", "transactionCode.code", "transactionCoding.transactionCode")
                acq_disp = _first(leg, "amounts.acquiredDisposedCode", "transactionAcquiredDisposedCode")
                shares   = _first(leg, "amounts.shares")
                price    = _first(leg, "amounts.pricePerShare")
                post     = _first(leg, "postTransactionAmounts.sharesOwnedFollowingTransaction",
                                      "postTransactionAmounts.sharesOwnedFollowing")
                u_title  = _first(leg, "underlyingSecurity.title")
                u_shares = _first(leg, "underlyingSecurity.shares")

                rows.append({
                    **base,
                    "table":            "deriv",
                    "securityTitle":    _first(leg, "securityTitle", default=None),
                    "transactionDate":  _first(leg, "transactionDate", default=None),
                    "code":             code,
                    "acq_disp":         acq_disp,
                    "shares":           _to_num(shares),
                    "pricePerShare":    _to_num(price),
                    "post_shares":      _to_num(post),
                    "directOrIndirect": _first(leg, "ownershipNature.directOrIndirectOwnership", default=None),
                    "underlying_title": u_title,
                    "underlying_shares": _to_num(u_shares),
                    "direction":        _direction(code, acq_disp, "deriv", is_holding=False),
                })

            # --- Non-derivative HOLDINGS (Form 3/5) ---
            for h in (nd.get("holdings") or []):
                # holdings often only have 'post' style amounts; we treat as a holding snapshot
                shares = _first(h, "postTransactionAmounts.sharesOwnedFollowingTransaction",
                                   "postTransactionAmounts.sharesOwnedFollowing",
                                   "amountOwnedFollowingTransaction",
                                   "amountOwnedFollowing",
                                   "amountOwned",
                                   "sharesOwnedFollowingTransaction",
                                   "shares")
                rows.append({
                    **base,
                    "table":            "nonDeriv_hold",
                    "securityTitle":    _first(h, "securityTitle", default=None),
                    "transactionDate":  _first(h, "transactionDate", default=_first(filing, "periodOfReport")),
                    "code":             None,
                    "acq_disp":         None,
                    "shares":           _to_num(shares),
                    "pricePerShare":    math.nan,
                    "post_shares":      _to_num(shares),
                    "directOrIndirect": _first(h, "ownershipNature.directOrIndirectOwnership", default=None),
                    "underlying_title": None,
                    "underlying_shares": None,
                    "direction":        _direction(None, None, "nonDeriv_hold", is_holding=True),
                })

            # --- Derivative HOLDINGS (Form 3/5) ---
            dtab = filing.get("derivativeTable") or {}
            for h in (dtab.get("holdings") or []):
                shares = _first(h, "postTransactionAmounts.sharesOwnedFollowingTransaction",
                                   "postTransactionAmounts.sharesOwnedFollowing",
                                   "amountOwnedFollowingTransaction",
                                   "amountOwnedFollowing",
                                   "amountOwned",
                                   "sharesOwnedFollowingTransaction",
                                   "shares")
                rows.append({
                    **base,
                    "table":            "deriv_hold",
                    "securityTitle":    _first(h, "securityTitle", default=None),
                    "transactionDate":  _first(h, "transactionDate", default=_first(filing, "periodOfReport")),
                    "code":             None,
                    "acq_disp":         None,
                    "shares":           _to_num(shares),
                    "pricePerShare":    math.nan,
                    "post_shares":      _to_num(shares),
                    "directOrIndirect": _first(h, "ownershipNature.directOrIndirectOwnership", default=None),
                    "underlying_title": _first(h, "underlyingSecurity.title"),
                    "underlying_shares": _to_num(_first(h, "underlyingSecurity.shares")),
                    "direction":        _direction(None, None, "deriv_hold", is_holding=True),
                })

    df = pd.DataFrame(rows)
    if df.empty:
        if debug:
            print("[debug] No rows; check input shape/keys.")
        return df

    # Final computed fields
    df["value_usd"]     = (pd.to_numeric(df["shares"], errors="coerce").fillna(0) *
                           pd.to_numeric(df["pricePerShare"], errors="coerce").fillna(0))
    df["stake_change"]  = [_stake_change(s, p) for s, p in zip(df["shares"], df["post_shares"])]

    # Order for readability
    order = [
        "filedAt","periodOfReport","issuer_symbol","issuer_name","owner_name","owner_title",
        "table","securityTitle","transactionDate","code","acq_disp","direction",
        "shares","pricePerShare","value_usd","post_shares","stake_change",
        "directOrIndirect","underlying_title","underlying_shares",
        "accessionNo","owner_cik","issuer_cik","documentType","schemaVersion","id",
        "isDirector","isOfficer","isTenPercentOwner","role_score",
    ]
    cols = [c for c in order if c in df.columns] + [c for c in df.columns if c not in order]
    df = df[cols].sort_values(["filedAt","issuer_symbol","owner_name","transactionDate"],
                               ascending=[False, True, True, True]).reset_index(drop=True)
    return df