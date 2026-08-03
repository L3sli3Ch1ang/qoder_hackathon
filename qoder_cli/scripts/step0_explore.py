"""Step 0 — enumerate SWDA sectors and sample the mapped sectors' data.

Writes .research/step0_report.txt so we can lock the exact sector mapping and
confirm the shapes needed by build_swda_seed.py (job roles per sector, the
TSC/CCS skills + proficiency levels attached to a role, the K&A items used for
bridge derivation, and the Emerging/CASL flag distribution).
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx_util import Workbook  # noqa: E402

RESEARCH = Path(__file__).resolve().parent.parent / ".research"
MAIN = RESEARCH / "skills_framework_dataset.xlsx"
UNIQUE = RESEARCH / "unique_skills_list.xlsx"
OUT = RESEARCH / "step0_report.txt"

# Candidate mapping to verify against the real sector list.
SECTOR_MAP = {
    "finance": ["Financial Services"],
    "ict": ["Infocomm Technology"],
    "healthcare": ["Healthcare"],
    "engineering": ["Engineering Services"],
    "sustainability": ["Carbon Services and Trading", "Environmental Services"],
}

lines: list[str] = []


def add(s: str = "") -> None:
    lines.append(s)


with Workbook(MAIN) as wb:
    add("=" * 100)
    add("DISTINCT SECTORS (from 'Job Role_Description')")
    add("=" * 100)
    _hdr, roles = wb.read_records("Job Role_Description")
    sector_roles: dict[str, list[dict]] = defaultdict(list)
    for rec in roles:
        sector_roles[rec.get("Sector", "").strip()].append(rec)
    for sec in sorted(sector_roles):
        add(f"  {sec!r}: {len(sector_roles[sec])} job roles")

    add()
    add("=" * 100)
    add("MAPPING VERIFICATION")
    add("=" * 100)
    all_sectors = set(sector_roles)
    for sid, names in SECTOR_MAP.items():
        for nm in names:
            status = "OK " if nm in all_sectors else "MISSING"
            add(f"  [{status}] {sid} <- {nm!r}")

    # Job Role -> skills (with PL + type) from 'Job Role_TSC_CCS'
    add()
    add("=" * 100)
    add("JOB ROLE -> TSC/CCS SKILLS (sample from 'Job Role_TSC_CCS')")
    add("=" * 100)
    _h2, links = wb.read_records("Job Role_TSC_CCS")
    role_skills: dict[tuple, list[dict]] = defaultdict(list)
    for rec in links:
        key = (rec.get("Sector", "").strip(), rec.get("Job Role", "").strip())
        role_skills[key].append({
            "title": rec.get("TSC_CCS Title", "").strip(),
            "type": rec.get("TSC_CCS Type", "").strip(),
            "pl": rec.get("Proficiency Level", "").strip(),
        })
    # Show one sample role per mapped sector
    for sid, names in SECTOR_MAP.items():
        for nm in names:
            sample = next((k for k in role_skills if k[0] == nm), None)
            if not sample:
                add(f"  ({sid}/{nm}: no role-skill links found)")
                continue
            skills = role_skills[sample]
            add(f"  {sid} | {sample[1][:50]}  ({len(skills)} skills)")
            for s in skills[:8]:
                add(f"      - {s['title'][:42]:42} [{s['type']}] PL{s['pl']}")

    # K&A structure sample
    add()
    add("=" * 100)
    add("K&A STRUCTURE (sample titles + item counts from 'TSC_CCS_K&A')")
    add("=" * 100)
    _h3, ka = wb.read_records("TSC_CCS_K&A")
    title_items: dict[str, set] = defaultdict(set)
    pl_desc: dict[tuple, str] = {}
    for rec in ka:
        title = rec.get("TSC_CCS Title", "").strip()
        item = rec.get("Knowledge / Ability Items", "").strip()
        if title and item:
            title_items[title].add(item)
        pl = rec.get("Proficiency Level", "").strip()
        pd = rec.get("Proficiency Description", "").strip()
        if pl and pd and (title, pl) not in pl_desc:
            pl_desc[(title, pl)] = pd
    add(f"  distinct skill titles with K&A items: {len(title_items)}")
    sample_titles = sorted(title_items, key=lambda t: -len(title_items[t]))[:5]
    for t in sample_titles:
        add(f"  {t[:50]:50} -> {len(title_items[t])} distinct K&A items")
    add("  sample proficiency descriptions (one skill across levels):")
    if sample_titles:
        st = sample_titles[0]
        for pl in ["1", "2", "3", "4", "5", "6"]:
            d = pl_desc.get((st, pl), "")
            if d:
                add(f"      PL{pl}: {d[:80]}")

    # TSC_CCS_Key: type distribution + a few titles
    add()
    add("=" * 100)
    add("TSC_CCS_Key type distribution")
    add("=" * 100)
    _h4, keys = wb.read_records("TSC_CCS_Key")
    type_counts = Counter(rec.get("TSC_CCS Type", "").strip() for rec in keys)
    add(f"  types: {dict(type_counts)}")
    title_type: dict[str, str] = {}
    title_desc: dict[str, str] = {}
    title_sector: dict[str, set] = defaultdict(set)
    for rec in keys:
        t = rec.get("TSC_CCS Title", "").strip()
        title_type.setdefault(t, rec.get("TSC_CCS Type", "").strip())
        title_desc.setdefault(t, rec.get("TSC_CCS Description", "").strip())
        title_sector[t].add(rec.get("Sector", "").strip())
    add(f"  distinct skill titles in Key: {len(title_type)}")

with Workbook(UNIQUE) as wb2:
    add()
    add("=" * 100)
    add("UNIQUE SKILLS LIST — Emerging/CASL distribution")
    add("=" * 100)
    _h5, uskills = wb2.read_records("Unique Skills List")
    emerg = Counter(rec.get("Emerging Skills", "").strip() for rec in uskills)
    casl = Counter(rec.get("CASL Skills", "").strip() for rec in uskills)
    add(f"  Emerging Skills values: {dict(emerg)}")
    add(f"  CASL Skills values: {dict(casl)}")
    add(f"  total unique skills: {len(uskills)}")
    # build a lookup of title -> (emerging, casl)
    flag_lookup: dict[str, tuple[str, str]] = {}
    for rec in uskills:
        t = rec.get("skill_title", "").strip()
        flag_lookup[t] = (rec.get("Emerging Skills", "").strip(), rec.get("CASL Skills", "").strip())
    add("  sample flagged skills:")
    shown = 0
    for rec in uskills:
        if rec.get("Emerging Skills", "").strip() == "1" or rec.get("CASL Skills", "").strip() == "1":
            add(f"      {rec.get('skill_title','')[:45]:45} E={rec.get('Emerging Skills','')} C={rec.get('CASL Skills','')}")
            shown += 1
            if shown >= 8:
                break

OUT.write_text("\n".join(lines), encoding="utf-8")
print(f"WROTE {OUT} ({len(lines)} lines)")
