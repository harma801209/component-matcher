"""Add reviewed domestic timing PNs without replacing other brands or runtime data.

The checked-in manifest is a review boundary, not a part-number generator. Sources
are fetched during research, not on a member's search path. Unknown/conflicting
values stay blank. Reapplying replaces only identical (brand, model) pairs.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from sync_official_timing_brands import (
    CRYSTAL_DIR, base_row, finalize_rows, refresh_runtime_caches, write_csv_atomically,
)

MANIFEST = Path(__file__).with_name("catalog_sources") / "domestic_timing_verified.json"
OUTPUT = CRYSTAL_DIR / "国产晶振逐料号核验.csv"
PENDING_STATUS = "原厂逐料号已核验；P2P待工程确认"


def build_verified_rows(manifest_path: Path = MANIFEST):
    document = json.loads(manifest_path.read_text(encoding="utf-8"))
    if document.get("version") != 1 or not document.get("records"):
        raise ValueError("Empty or unsupported domestic timing manifest")
    rows, seen = [], set()
    for item in document["records"]:
        model = item["model"]
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9.\-]+", model) or model == item["series"]:
            raise ValueError(f"Not a complete ordering code: {model}")
        key = (item["brand"], model)
        if key in seen:
            raise ValueError(f"Duplicate reviewed PN: {key}")
        seen.add(key)
        fields = item["fields"]
        if fields.get("器件类型") not in {"晶振", "振荡器"}:
            raise ValueError(f"Not a timing component: {model}")
        if not re.fullmatch(r"\d+(?:\.\d+)?", fields.get("频率", "")):
            raise ValueError(f"Exact frequency required: {model}")
        if fields.get("频率单位") not in {"HZ", "KHZ", "MHZ"}:
            raise ValueError(f"Frequency unit required: {model}")
        if not item["source"].startswith("https://") or not item.get("evidence"):
            raise ValueError(f"Source evidence required: {model}")
        # An identity, lifecycle, grade, or match label cannot be smuggled in as
        # a specification field. These five records have no AEC evidence.
        if any(k in fields for k in ("品牌", "型号", "系列", "推荐等级", "型号粒度", "生产状态", "特殊用途", "AEC等级", "数据状态")):
            raise ValueError(f"Unexpected identity/qualification override: {model}")
        note = item["evidence"] + item["cautions"]
        rows.append(base_row(**fields, **{
            "品牌": item["brand"], "型号": model, "系列": item["series"],
            "系列说明": "圆柱音叉晶体" if item["series"] == "TF-206" else "小型石英晶体谐振器",
            "容值": fields["频率"], "容值单位": fields["频率单位"],
            "容值误差": "±" + fields["频差（ppm）"] + "ppm",
            "型号粒度": "官方逐料号", "官网链接": item["source"],
            "数据来源": "原厂逐料号规格书/页面（人工核验）",
            "数据状态": PENDING_STATUS, "校验时间": document["checked_at"],
            "校验备注": note, "备注1": "P2P待工程确认；" + note,
            "尺寸来源": item["evidence"],
        }))
    return finalize_rows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply-cache", action="store_true")
    args = parser.parse_args()
    frame = build_verified_rows()
    write_csv_atomically(frame, OUTPUT)
    print(f"source_csv={OUTPUT}", flush=True)
    print(f"reviewed_rows={len(frame)}", flush=True)
    if args.apply_cache:
        print(json.dumps(refresh_runtime_caches(frame, OUTPUT), ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
