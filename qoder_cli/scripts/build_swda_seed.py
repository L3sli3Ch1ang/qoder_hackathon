"""One-off generator: derive SkillBridge seed data from the official SWDA
Skills Framework dataset (downloaded into .research/).

Stdlib only (no pip in the NixOS dev venv). Reads:
  .research/skills_framework_dataset.xlsx
  .research/unique_skills_list.xlsx
Writes (deterministic; fixed seed):
  app/data/skill_registry.json   skill metadata + Emerging/CASL + PL descriptions
  app/data/skill_taxonomy.json   {sector_id: [skill titles]}
  app/data/jobs.json             30 real roles + skill_requirements {skill: PL}
  app/data/candidates.json       150 candidates + skill_levels {skill: PL}
  app/data/bridges.json          K&A-Jaccard-derived {gap: {via, confidence}}
  app/data/courses.json          SSG-style courses keyed to real skill titles

Run:  python scripts/build_swda_seed.py
"""

from __future__ import annotations

import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import quote_plus

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx_util import Workbook  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RESEARCH = ROOT / ".research"
DATA = ROOT / "app" / "data"
MAIN = RESEARCH / "skills_framework_dataset.xlsx"
UNIQUE = RESEARCH / "unique_skills_list.xlsx"

random.seed(20260729)

# ---------------------------------------------------------------------------
# Verified sector mapping (Step 0 confirmed every name exists in the workbook).
# SkillBridge sector id -> list of SWDA sector names to draw from.
# ---------------------------------------------------------------------------
SECTOR_MAP: dict[str, list[str]] = {
    "finance": ["Financial Services"],
    "ict": ["Infocomm Technology"],
    "healthcare": ["Healthcare"],
    "engineering": ["Engineering Services"],
    "sustainability": ["Carbon Services and Trading", "Environmental Services"],
}

JOBS_PER_SECTOR = 6
CANDIDATES_PER_SECTOR = 30

# CCS (Critical Core Skills) use textual proficiency levels; map onto the 1-6
# scale used by TSC skills so the whole matcher works on one numeric axis.
CCS_PL_MAP = {
    "foundation": 1,
    "basic": 2,
    "intermediate": 3,
    "advanced": 5,
}

# Realistic Singapore course providers for synthesized (grounded) course entries.
PROVIDERS = [
    "SkillsFuture Singapore (SSG)",
    "NTU LearningHub",
    "NUS School of Continuing Education",
    "Singapore Polytechnic (SP)",
    "Temasek Polytechnic",
    "Institute of Adult Learning (IAL)",
    "SMU Academy",
    "Republic Polytechnic",
]

# Sector-flavoured certification pools (illustrative, real cert names).
CERT_POOL = {
    "finance": ["CFA", "ACCA", "CPA Singapore", "FRM", "CAMS", "MAS Compliance Cert"],
    "ict": ["AWS Solutions Architect", "CKA (Kubernetes)", "CISSP", "Google Cloud Pro", "Azure Admin", "PMP"],
    "healthcare": ["RN License", "CPHIMS", "ACRP Clinical Research", "HSA Regulatory Cert", "BLS/ACLS", "Lean Healthcare"],
    "engineering": ["PE (Professional Engineer)", "Six Sigma Green Belt", "PMP", "Certified Energy Manager", "NEBOSH", "SCADA Cert"],
    "sustainability": ["ISO 14064 Lead Verifier", "GRI Certified", "LEED Green Associate", "BCA Green Mark Pro", "CFA ESG", "Carbon Markets Cert"],
}

# Deterministic name pools (multicultural Singapore-style).
FIRST_NAMES = [
    "Wei", "Jia", "Ming", "Hui", "Xin", "Jun", "Yan", "Kai", "Ling", "Rui",
    "Aarav", "Priya", "Arjun", "Divya", "Rohan", "Meera", "Karan", "Ananya",
    "Muhammad", "Nurul", "Aisyah", "Hafiz", "Farhan", "Siti", "Danial", "Amirah",
    "James", "Sarah", "Daniel", "Rachel", "Marcus", "Nicole", "Kevin", "Chloe",
]
LAST_NAMES = [
    "Tan", "Lim", "Wong", "Ng", "Ong", "Chong", "Goh", "Lee", "Ho", "Koh",
    "Kumar", "Raj", "Singh", "Nair", "Menon",
    "Bin Ahmad", "Binti Hassan", "Bin Ismail", "Binti Rahman",
    "Smith", "Nguyen", "Garcia", "Wilson", "Yusof",
]


def parse_pl(raw: str) -> int:
    """Normalize a proficiency level to an int in 1-6.

    TSC skills store '1'..'6'; CCS skills store textual levels
    (Foundation/Basic/Intermediate/Advanced). Unknown values default to 3.
    """
    s = (raw or "").strip().lower()
    if s.isdigit():
        return max(1, min(6, int(s)))
    return CCS_PL_MAP.get(s, 3)


def clean_role_title(role: str) -> str:
    """Turn a verbose SWDA role string into a compact job title.

    'Audit Associate / Audit Assistant Associate' -> 'Audit Associate'
    'Assistant Engineer / Senior Technician (Commissioning)' -> 'Assistant Engineer'
    """
    title = role.strip()
    # Take the first alternative when roles are listed with ' / '.
    title = title.split(" / ")[0].strip()
    # Drop a trailing parenthetical qualifier.
    if "(" in title:
        title = title.split("(")[0].strip()
    return title or role.strip()


def _first_sentences(text: str, budget: int = 240) -> str:
    """Return complete sentences from ``text`` within ``budget`` characters.

    Never cuts mid-word or mid-sentence. Always includes the first sentence even
    if it exceeds the budget, so the result is always a complete thought ending
    in terminal punctuation (SWDA role descriptions often open with a single
    very long sentence listing every alternate role title). Keeps candidate
    summaries readable (the old ``[:140]`` hard slice produced dangling
    fragments like '...assumes the respo').
    """
    text = " ".join((text or "").split())
    if not text:
        return ""
    sentences = [s.strip() for s in re.findall(r"[^.!?]+[.!?]", text) if s.strip()]
    if not sentences:
        # No terminal punctuation anywhere: treat the whole text as one sentence.
        return text.rstrip(".!?") + "."
    out = []
    total = 0
    for s in sentences:
        if out and total + 1 + len(s) > budget:
            break
        out.append(s)
        total += len(s) + 1
    return " ".join(out)


# ---------------------------------------------------------------------------
# Load the workbooks into in-memory indices.
# ---------------------------------------------------------------------------
def load_indices():
    print("Reading main workbook (this parses ~150k rows)...")
    role_desc: dict[tuple[str, str], dict] = {}
    sector_roles: dict[str, list[str]] = defaultdict(list)
    role_skills: dict[tuple[str, str], dict[str, dict]] = defaultdict(dict)
    role_tasks: dict[tuple[str, str], list[str]] = defaultdict(list)
    title_meta: dict[str, dict] = {}
    title_ka: dict[str, set[str]] = defaultdict(set)
    title_pldesc: dict[tuple[str, int], str] = {}

    with Workbook(MAIN) as wb:
        # Job Role_Description
        _h, rows = wb.read_records("Job Role_Description")
        for r in rows:
            sector = r.get("Sector", "").strip()
            role = r.get("Job Role", "").strip()
            if not sector or not role:
                continue
            key = (sector, role)
            if key not in role_desc:
                role_desc[key] = {
                    "track": r.get("Track", "").strip(),
                    "description": r.get("Job Role Description", "").strip(),
                    "performance": r.get("Performance Expectation", "").strip(),
                }
                sector_roles[sector].append(role)

        # Job Role_TSC_CCS  (skill -> PL per role; keep max PL per title)
        _h, rows = wb.read_records("Job Role_TSC_CCS")
        for r in rows:
            sector = r.get("Sector", "").strip()
            role = r.get("Job Role", "").strip()
            title = r.get("TSC_CCS Title", "").strip()
            if not (sector and role and title):
                continue
            pl = parse_pl(r.get("Proficiency Level", ""))
            stype = r.get("TSC_CCS Type", "").strip().lower() or "tsc"
            entry = role_skills[(sector, role)].get(title)
            if entry is None or pl > entry["pl"]:
                role_skills[(sector, role)][title] = {"pl": pl, "type": stype}

        # Job Role_CWF_KT  (key tasks per role)
        _h, rows = wb.read_records("Job Role_CWF_KT")
        for r in rows:
            sector = r.get("Sector", "").strip()
            role = r.get("Job Role", "").strip()
            task = r.get("Key Tasks", "").strip()
            if sector and role and task:
                tasks = role_tasks[(sector, role)]
                if task not in tasks:
                    tasks.append(task)

        # TSC_CCS_Key  (skill metadata)
        _h, rows = wb.read_records("TSC_CCS_Key")
        for r in rows:
            title = r.get("TSC_CCS Title", "").strip()
            if not title:
                continue
            meta = title_meta.setdefault(title, {
                "type": (r.get("TSC_CCS Type", "").strip().lower() or "tsc"),
                "description": r.get("TSC_CCS Description", "").strip(),
                "category": r.get("TSC_CCS Category", "").strip(),
                "sectors": set(),
            })
            sec = r.get("Sector", "").strip()
            if sec:
                meta["sectors"].add(sec)

        # TSC_CCS_K&A  (K&A items per skill + per-level proficiency descriptions)
        _h, rows = wb.read_records("TSC_CCS_K&A")
        for r in rows:
            title = r.get("TSC_CCS Title", "").strip()
            item = r.get("Knowledge / Ability Items", "").strip()
            if title and item:
                title_ka[title].add(item)
            pl = parse_pl(r.get("Proficiency Level", ""))
            pd = r.get("Proficiency Description", "").strip()
            if title and pd and (title, pl) not in title_pldesc:
                title_pldesc[(title, pl)] = pd

    print("Reading unique skills list (Emerging/CASL flags)...")
    flags: dict[str, dict] = {}
    with Workbook(UNIQUE) as wb2:
        _h, rows = wb2.read_records("Unique Skills List")
        for r in rows:
            title = r.get("skill_title", "").strip()
            if not title:
                continue
            flags[title] = {
                "emerging": r.get("Emerging Skills", "").strip() == "1",
                "casl": r.get("CASL Skills", "").strip() == "1",
            }

    return {
        "role_desc": role_desc,
        "sector_roles": sector_roles,
        "role_skills": role_skills,
        "role_tasks": role_tasks,
        "title_meta": title_meta,
        "title_ka": title_ka,
        "title_pldesc": title_pldesc,
        "flags": flags,
    }


# ---------------------------------------------------------------------------
# Job selection
# ---------------------------------------------------------------------------
def select_jobs(idx):
    """Pick JOBS_PER_SECTOR real roles per sector (roles with >=5 skills)."""
    jobs = []
    chosen_roles_by_sector: dict[str, list[tuple[str, str]]] = {}
    counter = 0
    for sid, swda_names in SECTOR_MAP.items():
        candidates = []
        for swda in swda_names:
            for role in idx["sector_roles"].get(swda, []):
                skills = idx["role_skills"].get((swda, role), {})
                if len(skills) >= 5:
                    candidates.append((swda, role))
        # Deterministic, varied pick: sort then stride through the list.
        candidates.sort()
        if len(candidates) > JOBS_PER_SECTOR:
            stride = len(candidates) / JOBS_PER_SECTOR
            picked = [candidates[int(i * stride)] for i in range(JOBS_PER_SECTOR)]
        else:
            picked = candidates[:JOBS_PER_SECTOR]
        chosen_roles_by_sector[sid] = picked
        for swda, role in picked:
            counter += 1
            skills = idx["role_skills"][(swda, role)]
            skill_requirements = {t: v["pl"] for t, v in sorted(skills.items())}
            desc = idx["role_desc"].get((swda, role), {})
            tasks = idx["role_tasks"].get((swda, role), [])[:6]
            jobs.append({
                "id": f"jd_{counter:03d}",
                "title": clean_role_title(role),
                "sector": sid,
                "skills_required": sorted(skill_requirements.keys()),
                "skill_requirements": skill_requirements,
                "key_tasks": tasks,
                "description": desc.get("description", "") or f"{clean_role_title(role)} role in the {swda} sector.",
                "_swda_sector": swda,
                "_swda_role": role,
            })
    return jobs, chosen_roles_by_sector


# ---------------------------------------------------------------------------
# Candidates
# ---------------------------------------------------------------------------
def build_candidates(idx, chosen_roles_by_sector):
    """Generate CANDIDATES_PER_SECTOR candidates per sector, anchored to real
    roles in that sector, with skill_levels derived from real role requirements."""
    candidates = []
    counter = 0
    name_idx = 0
    for sid, swda_names in SECTOR_MAP.items():
        # Pool of real roles in this sector that have enough skills.
        pool = []
        for swda in swda_names:
            for role in idx["sector_roles"].get(swda, []):
                if len(idx["role_skills"].get((swda, role), {})) >= 5:
                    pool.append((swda, role))
        pool.sort()
        if not pool:
            continue
        certs = CERT_POOL[sid]
        for i in range(CANDIDATES_PER_SECTOR):
            counter += 1
            swda, role = pool[i % len(pool)]
            role_skill_map = idx["role_skills"][(swda, role)]
            # Seniority level for this candidate (1-6), skewed to mid levels.
            level = random.choices([2, 3, 3, 4, 4, 5], k=1)[0]
            # Decide which of the role's skills the candidate actually has, and
            # at what proficiency (varied around the role's required level).
            skill_levels: dict[str, int] = {}
            for title, info in sorted(role_skill_map.items()):
                if random.random() < 0.78:  # candidate covers ~78% of the role
                    req = info["pl"]
                    delta = random.choices([-1, 0, 0, 1], k=1)[0]
                    cand_pl = max(1, min(6, req + delta + (level - 3) // 2))
                    skill_levels[title] = cand_pl
            if len(skill_levels) < 4:  # ensure a usable profile
                for title, info in sorted(role_skill_map.items()):
                    skill_levels.setdefault(title, max(1, min(6, info["pl"])))
                    if len(skill_levels) >= 5:
                        break
            skills = sorted(skill_levels.keys())
            avg_pl = sum(skill_levels.values()) / max(1, len(skill_levels))
            years = max(1, int(round((avg_pl - 1) * 3 + random.choice([0, 1, 2]))))
            first = FIRST_NAMES[name_idx % len(FIRST_NAMES)]
            last = LAST_NAMES[(name_idx * 7 + 3) % len(LAST_NAMES)]
            name_idx += 1
            n_cert = random.choice([0, 1, 1, 2])
            chosen_certs = random.sample(certs, k=min(n_cert, len(certs)))
            top_skills = sorted(skill_levels, key=lambda s: -skill_levels[s])[:3]
            title = clean_role_title(role)
            role_description = _first_sentences(
                idx['role_desc'].get((swda, role), {}).get('description', ''), 200
            )
            summary = (
                f"{title} with {years} years in the {swda} sector. "
                f"Strongest in {', '.join(top_skills)}. "
                f"{role_description}".strip()
            )
            candidates.append({
                "id": f"cand_{counter:03d}",
                "name": f"{first} {last}",
                "sector": sid,
                "title": title,
                "years_experience": years,
                "skills": skills,
                "skill_levels": skill_levels,
                "certifications": chosen_certs,
                "summary": summary,
            })
    return candidates


# ---------------------------------------------------------------------------
# Bridges (derived from K&A Jaccard similarity)
# ---------------------------------------------------------------------------
def jaccard(a: set, b: set) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def containment(a: set, b: set) -> float:
    """Fraction of a's items also present in b: |a ∩ b| / |a|.

    Directional measure answering 'how much of gap skill a is already covered
    by candidate skill b' — the right semantic for transferable bridges.
    """
    if not a:
        return 0.0
    return len(a & b) / len(a)


# Only emit bridges whose evidence (shared K&A coverage) clears this floor, so
# the UI never shows a meaningless near-zero-confidence bridge.
BRIDGE_FLOOR = 0.2


def build_bridges(idx, used_skills: set[str]):
    """For each used skill S, find the skill V whose K&A items best *cover* S
    (max containment |S ∩ V| / |S|) and emit {S: {via: V, confidence}}. Only
    bridges clearing BRIDGE_FLOOR are kept (evidence-based, not noise). CCS
    neighbours get a small boost because Critical Core Skills are officially
    cross-sector transferable.

    Returns (bridges, all_confidences) — the latter for distribution reporting.
    """
    title_ka = idx["title_ka"]
    title_meta = idx["title_meta"]
    skills = [s for s in sorted(used_skills) if title_ka.get(s)]
    bridges: dict[str, dict] = {}
    all_confs: list[float] = []
    for s in skills:
        s_set = title_ka[s]
        best_via = None
        best_score = 0.0
        for other in skills:
            if other == s:
                continue
            score = containment(s_set, title_ka[other])
            if score > best_score:
                best_score = score
                best_via = other
        if best_via is None or best_score <= 0.0:
            continue
        all_confs.append(best_score)
        if best_score < BRIDGE_FLOOR:
            continue
        conf = best_score
        # CCS boost: bridging via a Critical Core Skill is especially transferable.
        if title_meta.get(best_via, {}).get("type") == "ccs":
            conf = min(0.95, conf + 0.1)
        bridges[s] = {"via": best_via, "confidence": round(conf, 3)}
    return bridges, all_confs


# ---------------------------------------------------------------------------
# Courses (grounded placeholders keyed to real skill titles)
# ---------------------------------------------------------------------------
def build_courses(used_skills: set[str]):
    courses: dict[str, dict] = {}
    providers = sorted(PROVIDERS)
    for i, skill in enumerate(sorted(used_skills)):
        provider = providers[i % len(providers)]
        hours = random.choice([8, 12, 16, 20, 24, 32, 40])
        # Link straight to the MySkillsFuture course *search results* for this
        # skill. The legacy course-directory.html?keyword= URL now redirects to
        # the generic search page and drops the keyword, so use the live
        # courses.myskillsfuture.gov.sg/search?q= endpoint instead.
        query = quote_plus(skill)
        courses[skill] = {
            "course_name": f"{skill} (SkillsFuture-aligned programme)",
            "provider": provider,
            "url": f"https://courses.myskillsfuture.gov.sg/search?q={query}",
            "duration_hours": hours,
        }
    return courses


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
def build_registry(idx, used_skills: set[str]):
    registry: dict[str, dict] = {}
    for title in sorted(used_skills):
        meta = idx["title_meta"].get(title, {})
        fl = idx["flags"].get(title, {"emerging": False, "casl": False})
        pl_desc = {}
        for pl in range(1, 7):
            d = idx["title_pldesc"].get((title, pl), "")
            if d:
                pl_desc[str(pl)] = d
        # Map SWDA sector names back to SkillBridge sector ids where applicable.
        sectors = set()
        for sid, swda_names in SECTOR_MAP.items():
            if any(n in meta.get("sectors", set()) for n in swda_names):
                sectors.add(sid)
        registry[title] = {
            "type": meta.get("type", "tsc"),
            "description": meta.get("description", ""),
            "category": meta.get("category", ""),
            "sectors": sorted(sectors),
            "emerging": bool(fl["emerging"]),
            "casl": bool(fl["casl"]),
            "proficiency_descriptions": pl_desc,
        }
    return registry


def write_json(name: str, obj) -> None:
    path = DATA / name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    print(f"  wrote {path.name}")


def main():
    idx = load_indices()

    print("Selecting jobs...")
    jobs, chosen = select_jobs(idx)

    print("Building candidates...")
    candidates = build_candidates(idx, chosen)

    # Taxonomy = union of skill titles per sector across its selected jobs.
    taxonomy: dict[str, list[str]] = {sid: set() for sid in SECTOR_MAP}
    for job in jobs:
        taxonomy[job["sector"]].update(job["skill_requirements"].keys())
    taxonomy = {sid: sorted(s) for sid, s in taxonomy.items()}

    used_skills: set[str] = set()
    for skills in taxonomy.values():
        used_skills.update(skills)
    # Also include every skill a candidate actually has, so bridges/courses cover them.
    for c in candidates:
        used_skills.update(c["skills"])

    print("Deriving bridges (K&A containment)...")
    bridges, all_confs = build_bridges(idx, used_skills)

    print("Building courses + registry...")
    courses = build_courses(used_skills)
    registry = build_registry(idx, used_skills)

    # Strip internal keys from jobs before writing.
    for job in jobs:
        job.pop("_swda_sector", None)
        job.pop("_swda_role", None)

    print("Writing outputs...")
    write_json("skill_registry.json", registry)
    write_json("skill_taxonomy.json", taxonomy)
    write_json("jobs.json", jobs)
    write_json("candidates.json", candidates)
    write_json("bridges.json", bridges)
    write_json("courses.json", courses)

    # Summary report
    confs = [b["confidence"] for b in bridges.values()]
    all_sorted = sorted(all_confs)

    def pct(p: float) -> float:
        if not all_sorted:
            return 0.0
        k = min(len(all_sorted) - 1, int(p * len(all_sorted)))
        return all_sorted[k]

    thresholds = [0.1, 0.2, 0.3, 0.5]
    above = {t: sum(1 for c in all_sorted if c >= t) for t in thresholds}
    report = [
        "SWDA seed build summary",
        "=======================",
        f"jobs: {len(jobs)} (target {JOBS_PER_SECTOR * len(SECTOR_MAP)})",
        f"candidates: {len(candidates)} (target {CANDIDATES_PER_SECTOR * len(SECTOR_MAP)})",
        f"taxonomy skills per sector: " + ", ".join(f"{k}={len(v)}" for k, v in taxonomy.items()),
        f"used skills universe: {len(used_skills)}",
        f"bridges emitted (floor={BRIDGE_FLOOR}): {len(bridges)}",
        f"bridge confidence (emitted): min={min(confs):.3f} max={max(confs):.3f} "
        f"mean={sum(confs)/len(confs):.3f}" if confs else "bridges emitted: none",
        f"raw containment distribution: p25={pct(0.25):.3f} p50={pct(0.50):.3f} "
        f"p75={pct(0.75):.3f} p90={pct(0.90):.3f} max={pct(1.0):.3f}",
        f"skills above thresholds: " + ", ".join(f">={t}:{above[t]}" for t in thresholds),
        f"courses: {len(courses)}",
        f"registry: {len(registry)} skills "
        f"(emerging={sum(1 for r in registry.values() if r['emerging'])}, "
        f"casl={sum(1 for r in registry.values() if r['casl'])})",
    ]
    print("\n".join(report))
    (RESEARCH / "build_report.txt").write_text("\n".join(report), encoding="utf-8")


if __name__ == "__main__":
    main()
