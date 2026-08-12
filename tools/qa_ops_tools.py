"""QA inspection ops tools — checklists, defect taxonomy, supplier CAPA drafts."""

from __future__ import annotations

import uuid
from typing import Any


def qa_defect_taxonomy(category: str = "general") -> dict[str, Any]:
    """Return defect codes for a product category (inspection vocabulary)."""
    base = [
        "DIM_OUT_OF_SPEC",
        "WEIGHT_OUT_OF_SPEC",
        "COSMETIC_SCRATCH",
        "COSMETIC_STAIN",
        "FUNCTION_FAIL",
        "PACKAGING_DAMAGE",
        "LABEL_MISSING",
        "ODOR",
        "SAFETY_CONCERN",
        "WRONG_ITEM",
    ]
    extra = {
        "textile": ["SIZING", "PILLING", "SEAM_FAIL", "COLOR_BLEED"],
        "electronics": ["BATTERY_SWELL", "PORT_FAIL", "OVERHEAT"],
        "kit": ["MISSING_COMPONENT", "ZIPPER_FAIL", "FOAM_COLLAPSE"],
    }.get((category or "general").lower(), [])
    return {"ok": True, "category": category or "general", "codes": base + extra}


def qa_run_inspection_checklist(
    sku: str,
    sample_id: str = "",
    category: str = "general",
    notes: str = "",
    defects: list[str] | None = None,
) -> dict[str, Any]:
    """Score a sample inspection and suggest PASS|CONDITIONAL|FAIL."""
    defs = list(defects or [])
    notes_l = (notes or "").lower()
    if "safety" in notes_l or "SAFETY_CONCERN" in defs:
        verdict = "FAIL"
        ship_hold = True
    elif len(defs) >= 3 or "FUNCTION_FAIL" in defs or "ZIPPER_FAIL" in defs:
        verdict = "CONDITIONAL" if len(defs) < 5 else "FAIL"
        ship_hold = True
    elif defs:
        verdict = "CONDITIONAL"
        ship_hold = True
    else:
        verdict = "PASS"
        ship_hold = False
    return {
        "ok": True,
        "inspection_id": f"qa_{uuid.uuid4().hex[:10]}",
        "sku": sku,
        "sample_id": sample_id or "unspecified",
        "verdict": verdict,
        "ship_hold": ship_hold,
        "defects": defs,
        "checklist": [
            "dimensions_weight",
            "function_cycles",
            "cosmetics",
            "packaging_label",
            "safety_category_flags",
        ],
        "notes": notes,
        "next": "Emit QAInspectionReport; CAPA if not PASS; Linear dual-write.",
    }


def qa_supplier_feedback_draft(
    sku: str,
    verdict: str,
    defects: list[str] | None = None,
    deadline_days: int = 7,
) -> dict[str, Any]:
    """Draft supplier CAPA / feedback email body (send is human/HITL)."""
    defs = ", ".join(defects or []) or "see inspection notes"
    body = (
        f"Subject: QC feedback — {sku} ({verdict})\n\n"
        f"We completed sample inspection for {sku}. Verdict: {verdict}.\n"
        f"Defects/codes: {defs}.\n"
        f"Please confirm CAPA within {deadline_days} days and ship a revised sample "
        f"before bulk PO release. Attach process photos where relevant.\n"
    )
    return {
        "ok": True,
        "draft_only": True,
        "sku": sku,
        "verdict": verdict,
        "body": body,
        "hitl": "Human sends to supplier; agent does not auto-email external vendors.",
    }


def get_qa_ops_tools() -> list:
    return [qa_defect_taxonomy, qa_run_inspection_checklist, qa_supplier_feedback_draft]
