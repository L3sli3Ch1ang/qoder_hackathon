"""Unit tests for course mapper module."""


def test_course_mapper_known_skill():
    """Course mapper returns course info for a known SWDA skill."""
    from app.pipeline.course_mapper import CourseMapper

    mapper = CourseMapper()
    results = mapper.run(["Business Planning"])
    assert len(results) == 1
    assert results[0]["skill"] == "Business Planning"
    assert "course_name" in results[0]
    assert "url" in results[0]
    assert results[0]["duration_hours"] is not None


def test_course_url_targets_search_results():
    """Course URLs deep-link to the MySkillsFuture search results for the skill.

    The legacy course-directory.html?keyword= URL redirects to the generic
    search page and drops the keyword; links must use the live
    courses.myskillsfuture.gov.sg/search?q= endpoint instead.
    """
    from urllib.parse import quote_plus

    from app.pipeline.course_mapper import CourseMapper

    mapper = CourseMapper()
    results = mapper.run(["Data Governance"])
    url = results[0]["url"]
    assert url.startswith("https://courses.myskillsfuture.gov.sg/search?q=")
    assert quote_plus("Data Governance") in url
    assert "course-directory.html" not in url


def test_course_mapper_unknown_skill():
    """Course mapper returns fallback for unknown skill."""
    from app.pipeline.course_mapper import CourseMapper

    mapper = CourseMapper()
    results = mapper.run(["Underwater Basket Weaving"])
    assert len(results) == 1
    assert "No mapped course" in results[0]["course_name"]
    assert results[0]["duration_hours"] is None


def test_course_mapper_multiple_skills():
    """Course mapper handles multiple gap skills."""
    from app.pipeline.course_mapper import CourseMapper

    mapper = CourseMapper()
    results = mapper.run(["Business Planning", "Data Governance", "Unknown Skill"])
    assert len(results) == 3


def test_course_mapper_empty_input():
    """Course mapper handles empty gap list."""
    from app.pipeline.course_mapper import CourseMapper

    mapper = CourseMapper()
    results = mapper.run([])
    assert results == []


def test_data_loader_candidates():
    """Data loader returns 150 candidates."""
    from app.data import get_candidates

    candidates = get_candidates()
    assert len(candidates) == 150


def test_data_loader_jobs():
    """Data loader returns 30 jobs."""
    from app.data import get_jobs

    jobs = get_jobs()
    assert len(jobs) == 30


def test_data_loader_courses():
    """Data loader returns 30+ course mappings."""
    from app.data import get_courses

    courses = get_courses()
    assert len(courses) >= 30


def test_data_loader_bridges():
    """Data loader returns 30+ bridge mappings."""
    from app.data import get_bridges

    bridges = get_bridges()
    assert len(bridges) >= 30
