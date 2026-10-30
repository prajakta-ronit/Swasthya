import pandas as pd


def col(df, names):
    normalized = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}
    return next((normalized[n] for n in names if n in normalized), None)


def compare_reports(old_df, new_df):
    ot, nt = col(old_df, ["test", "test_name", "parameter", "name", "investigation"]), col(new_df, ["test", "test_name", "parameter", "name", "investigation"])
    ov, nv = col(old_df, ["value", "result", "test_value", "measurement"]), col(new_df, ["value", "result", "test_value", "measurement"])
    ou, nu = col(old_df, ["unit", "units"]), col(new_df, ["unit", "units"])
    orange, nrange = col(old_df, ["reference_range", "reference", "normal_range", "range"]), col(new_df, ["reference_range", "reference", "normal_range", "range"])
    if not all([ot, nt, ov, nv]):
        raise ValueError(f"Could not identify test/value columns. Previous: {list(old_df.columns)}; Current: {list(new_df.columns)}")

    old = pd.DataFrame({
        "_key": old_df[ot].fillna("").astype(str).str.strip().str.casefold(),
        "Test": old_df[ot].astype(str),
        "Previous Value": pd.to_numeric(old_df[ov].astype(str).str.replace(",", "", regex=False), errors="coerce"),
        "Previous Unit": old_df[ou].fillna("").astype(str).str.strip() if ou else "",
    })
    new = pd.DataFrame({
        "_key": new_df[nt].fillna("").astype(str).str.strip().str.casefold(),
        "Current Test": new_df[nt].astype(str),
        "Current Value": pd.to_numeric(new_df[nv].astype(str).str.replace(",", "", regex=False), errors="coerce"),
        "Current Unit": new_df[nu].fillna("").astype(str).str.strip() if nu else "",
    })
    if orange:
        old["Previous Reference Range"] = old_df[orange].astype(str)
    if nrange:
        new["Current Reference Range"] = new_df[nrange].astype(str)

    old = old[old["_key"] != ""].drop_duplicates("_key", keep="last")
    new = new[new["_key"] != ""].drop_duplicates("_key", keep="last")
    out = old.merge(new, on="_key", how="outer", indicator=True)
    out["Match Status"] = out["_merge"].map({
        "both": "Matched",
        "left_only": "Only in previous report",
        "right_only": "Only in current report",
    }).astype("string")
    out["Units Compatible"] = (
        out["Previous Unit"].fillna("").astype(str).str.strip().str.casefold()
        == out["Current Unit"].fillna("").astype(str).str.strip().str.casefold()
    ) | out["Previous Unit"].fillna("").astype(str).str.strip().eq("") | out["Current Unit"].fillna("").astype(str).str.strip().eq("")
    numeric = out["Previous Value"].notna() & out["Current Value"].notna() & out["Units Compatible"]
    out["Change"] = (out["Current Value"] - out["Previous Value"]).where(numeric).round(3)
    out["Percentage Change (%)"] = (out["Change"] / out["Previous Value"].where(out["Previous Value"].ne(0)) * 100).round(2)
    out.loc[~out["Units Compatible"], "Match Status"] = "Unit mismatch — not compared"
    return out.drop(columns=["_key", "_merge"])
