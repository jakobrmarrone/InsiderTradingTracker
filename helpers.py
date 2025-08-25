import json
import pandas as pd
"""

This is trash code I reference 

"""
#Safe text search in footnotes 

def has_10b5_1(footnotes):
    if not isinstance(footnotes, list):
        return False
    return any("10b5-1" in (fn.get("text") or "").lower() for fn in footnotes)

def has_weighted_avg(footnotes):
    if not isinstance(footnotes, list):
        return False
    return any("weighted average" in (fn.get("text") or "").lower() for fn in footnotes)

ROLE_MAP = {
    "chief executive officer": 1.00, "ceo": 1.00, "president": 0.90, "chair": 0.90,
    "chief financial officer": 0.85, "cfo": 0.85, "chief operating officer": 0.80, "coo": 0.80,
    "general counsel": 0.75, "principal accounting officer": 0.75,
    "senior vice president": 0.70, "svp": 0.70, "vice president": 0.60, "vp": 0.60,
    "director": 0.60, "ten percent owner": 0.90
}

def role_score(relationship: dict) -> float:
    rel = relationship or {}
    title = (rel.get('officerTitle') or '').lower()

    for key, score in ROLE_MAP.items():
        if key in title: 
            return score 
    if rel.get('isOfficer'):
        return 0.5
    if rel.get('isTenPercentOwner'):
        return 0.90
    if rel.get('isDirector'):
        return 0.6
    return 0.3

#Normalize transaction semantics into buy/sell ish buckets 
def direction_from(code, acq_disp):
    code = (code or '').upper()
    ad = (acq_disp or '').upper()

    if code == 'P' or ad == 'A':
        return 'BUYish'
    if code == 'S' or ad == 'D':
        return 'SELLish'
    if code == 'F':
        return 'TaxWithHold'
    if code == 'M':
        return 'Option/RSU'
    return code or ad or 'Other'

def stake_change(shares, post_shares):
    try:
        s = float(shares or 0)
        p = float(post_shares or 0)
        return s / (s + p) if (s + p) > 0 else 0.0
    except Exception:
        return 0.0 
    

import pandas as pd

import pandas as pd

def flatten_insider_payload(payload) -> pd.DataFrame:
    """Flatten sec-api insider payload into one row per transaction leg."""
    rows = []

    # Normalize top-level container
    if isinstance(payload, dict):
        filings = payload.get("transactions", [])
    elif isinstance(payload, list):
        filings = payload
    else:
        filings = []

    for filing in filings:
        issuer = filing.get("issuer") or {}
        owner  = filing.get("reportingOwner") or {}
        rel    = owner.get("relationship") or {}

        base = {
            "accessionNo":      filing.get("accessionNo"),
            "filedAt":          filing.get("filedAt"),
            "periodOfReport":   filing.get("periodOfReport"),
            "issuer_symbol":    issuer.get("tradingSymbol"),
            "issuer_name":      issuer.get("name"),
            "issuer_cik":       issuer.get("cik"),
            "owner_name":       owner.get("name"),
            "owner_cik":        owner.get("cik"),
            "owner_title":      rel.get("officerTitle"),
            "isDirector":       rel.get("isDirector"),
            "isOfficer":        rel.get("isOfficer"),
            "isTenPercentOwner":rel.get("isTenPercentOwner"),
        }

        # --- Non-derivative legs
        nd_legs = (filing.get("nonDerivativeTable") or {}).get("transactions") or []
        for leg in nd_legs:
            amounts = leg.get("amounts") or {}
            post    = leg.get("postTransactionAmounts") or {}
            own     = leg.get("ownershipNature") or {}
            rows.append({
                **base,
                "table": "nonDeriv",
                "securityTitle":   leg.get("securityTitle"),
                "transactionDate": leg.get("transactionDate"),
                "code":            (leg.get("coding") or {}).get("code"),
                "acq_disp":        amounts.get("acquiredDisposedCode"),   # 'A'/'D'
                "shares":          amounts.get("shares"),
                "pricePerShare":   amounts.get("pricePerShare"),
                "post_shares":     post.get("sharesOwnedFollowingTransaction"),
                "directOrIndirect":own.get("directOrIndirectOwnership"),
            })

        # --- Derivative legs
        d_legs = (filing.get("derivativeTable") or {}).get("transactions") or []
        for leg in d_legs:
            amounts = leg.get("amounts") or {}
            post    = leg.get("postTransactionAmounts") or {}
            own     = leg.get("ownershipNature") or {}
            under   = leg.get("underlyingSecurity") or {}
            rows.append({
                **base,
                "table": "deriv",
                "securityTitle":   leg.get("securityTitle"),
                "transactionDate": leg.get("transactionDate"),
                "code":            (leg.get("coding") or {}).get("code"),
                "acq_disp":        amounts.get("acquiredDisposedCode"),
                "shares":          amounts.get("shares"),
                "pricePerShare":   amounts.get("pricePerShare"),
                "post_shares":     post.get("sharesOwnedFollowingTransaction"),
                "directOrIndirect":own.get("directOrIndirectOwnership"),
                "underlying_shares": under.get("shares"),
                "underlying_title":  under.get("title"),
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df  # early exit so you can see it's truly empty

    # Type cleanup + simple computed fields
    df["shares"]        = pd.to_numeric(df["shares"], errors="coerce")
    df["pricePerShare"] = pd.to_numeric(df["pricePerShare"], errors="coerce")
    df["post_shares"]   = pd.to_numeric(df["post_shares"], errors="coerce")
    df["value_usd"]     = df["shares"].fillna(0) * df["pricePerShare"].fillna(0)

    def direction(code, acq_disp):
        c = (code or "").upper(); a = (acq_disp or "").upper()
        if c == "P" or a == "A": return "BUYish"
        if c == "S" or a == "D": return "SELLish"
        if c == "F": return "TaxWithhold"
        if c == "M": return "Option/RSU"
        return c or a or "Other"

    df["direction"] = [direction(c, a) for c, a in zip(df["code"], df["acq_disp"])]

    def stake_change(s, p):
        s = float(s or 0); p = float(p or 0)
        return (s / (s + p)) if (s + p) > 0 else 0.0

    df["stake_change"] = [stake_change(s, p) for s, p in zip(df["shares"], df["post_shares"])]

    df = df.sort_values(
        ["filedAt","issuer_symbol","owner_name","transactionDate"],
        ascending=[False, True, True, True]
    ).reset_index(drop=True)

    return df


