"""API request/response schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class MatchRequest(BaseModel):
    """Request body for POST /api/match."""

    jd_text: str = Field(..., min_length=1, description="Job description text to match against")
    mode: Literal["ranked", "surprise"] = "ranked"
    perspective: Literal["recruiter", "candidate"] = "recruiter"
    added_skills: list[str] = Field(default_factory=list)
    removed_skills: list[str] = Field(default_factory=list)


class CourseInfo(BaseModel):
    """SSG course recommendation."""

    skill: str
    course_name: str
    provider: str
    url: str
    duration_hours: int | None = None


class BridgeInfo(BaseModel):
    """Bridge skill mapping."""

    gap_skill: str
    via_skill: str
    confidence: float


class MatchedSkillDetail(BaseModel):
    """Proficiency comparison for a single matched skill."""

    skill: str
    required_pl: int | None = None
    candidate_pl: int | None = None
    met: bool = True


class MatchResult(BaseModel):
    """A single match result."""

    candidate_id: str
    name: str
    title: str
    sector: str
    years_experience: int = 0
    score: int
    narrative: str
    matched: list[str]
    gap: list[str]
    bridge: list[BridgeInfo]
    courses: list[CourseInfo]
    is_surprise: bool = False
    proficiency_fit: float | None = None
    matched_detail: list[MatchedSkillDetail] = Field(default_factory=list)
    emerging_skills: list[str] = Field(default_factory=list)
    casl_skills: list[str] = Field(default_factory=list)
    skills_detected: bool = True


class MatchResponse(BaseModel):
    """Response for POST /api/match."""

    results: list[MatchResult]
    mode: str
    total: int


class CandidateProfile(BaseModel):
    """Full candidate profile behind a match result (CV detail view)."""

    id: str
    name: str
    sector: str
    title: str
    years_experience: int = 0
    skills: list[str] = Field(default_factory=list)
    skill_levels: dict[str, int] = Field(default_factory=dict)
    certifications: list[str] = Field(default_factory=list)
    summary: str = ""
