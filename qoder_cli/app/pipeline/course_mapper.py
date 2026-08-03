"""Course mapper module."""

from app.data import get_courses

FALLBACK_URL = "https://www.skillsfuture.gov.sg/skills-framework"


class CourseMapper:
    """Map gap skills to SSG course recommendations."""

    def __init__(self) -> None:
        self._courses = get_courses()

    def run(self, gap_skills: list[str]) -> list[dict]:
        """Look up SSG courses for each gap skill.

        Args:
            gap_skills: List of skill names identified as gaps.

        Returns:
            List of dicts with keys: skill, course_name, provider, url, duration_hours.
        """
        results = []
        for skill in gap_skills:
            course = self._courses.get(skill)
            if course:
                results.append({
                    "skill": skill,
                    "course_name": course["course_name"],
                    "provider": course["provider"],
                    "url": course["url"],
                    "duration_hours": course["duration_hours"],
                })
            else:
                results.append({
                    "skill": skill,
                    "course_name": "No mapped course yet — explore SSG directory",
                    "provider": "SkillsFuture Singapore",
                    "url": FALLBACK_URL,
                    "duration_hours": None,
                })
        return results
