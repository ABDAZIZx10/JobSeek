from keybert import KeyBERT
import spacy
from playwright.async_api import Locator

GENERIC_KEYWORDS = {
    "engineer",
    "developer",
    "software",
    "job",
    "role",
    "skills",
    "experience",
}

TECH_KEYWORDS ={
    "C++",
    "C#",
    ".NET",
    "k8s",
    "Kubernetes",
    "FastAPI",
    "React",
    "PostgreSQL",
    "Docker"
}

spacy_model = None


def get_spacy_model():
    global spacy_model

    if spacy_model is None:
        spacy_model = spacy.blank("en")
        ruler = spacy_model.add_pipe(
            "entity_ruler",
            config={"phrase_matcher_attr": "LOWER"},
        )
        patterns = [
            {"label": "SKILL", "pattern": tech}
            for tech in TECH_KEYWORDS
        ]
        ruler.add_patterns(patterns)

    return spacy_model


def extractTechSkills(text: str):
    doc = get_spacy_model()(text)
    skills = []

    for entity in doc.ents:
        if entity.label_ == "SKILL" and entity.text not in skills:
            skills.append(entity.text)

    return skills


def _scrape_status(value):
    return "OK" if value else "MISS"


def log_job(i, total, job_info):
    details = job_info.get("details") or {}
    has_criteria = any(
        key not in ("num_applicants", "description") for key in details
    )

    print(f"[{i + 1}/{total}] {job_info.get('title') or '?'} @ {job_info.get('company') or '?'}")
    print(
        f"  list     | title: {_scrape_status(job_info.get('title'))} "
        f"| company: {_scrape_status(job_info.get('company'))} "
        f"| location: {_scrape_status(job_info.get('location'))} "
        f"| date: {_scrape_status(job_info.get('date'))} "
        f"| url: {_scrape_status(job_info.get('Job Details URL'))}"
    )

    if not details:
        print("  details  | FAIL (page not scraped)")
        return

    print(
        f"  details  | description: {_scrape_status(details.get('description'))} "
        f"| applicants: {_scrape_status(details.get('num_applicants'))} "
        f"| criteria: {_scrape_status(has_criteria)}"
    )

async def safe_text(locator: Locator):
    try:
        if await locator.count() == 0:
            return None

        text = await locator.first.text_content(timeout=6000)
        return " ".join(text.split()) if text else None

    except:
        return None


async def safe_attr(locator: Locator, attr):
    try:
        if await locator.count() == 0:
            print("locator is empty")
            return None

        text = await locator.first.get_attribute(attr, timeout=6000)
        return text
    except Exception as E:
        print(f"an error occured getting the url information: {E} ")
        return None


def getKeywords(prompt: str, model):
    kw_model = KeyBERT(model)
    keywords = kw_model.extract_keywords(
        prompt.lower(),
        keyphrase_ngram_range=(1, 2),
        top_n=8,
        stop_words="english",
    )
    extracted_keywords = [
        key
        for key, score in keywords
        if not all(part in GENERIC_KEYWORDS for part in key.split())
    ]

    for skill in extractTechSkills(prompt):
        if skill.lower() not in [keyword.lower() for keyword in extracted_keywords]:
            extracted_keywords.append(skill)

    return extracted_keywords


def _keyword_found(keyword: str, text: str):
    if keyword in text:
        return True

    keyword_parts = keyword.split()
    return len(keyword_parts) > 1 and all(part in text for part in keyword_parts)


def boostKeywords(results, keywords, boost_amount=0.03, max_boost=0.15, limit=5):
    boosted_results = []

    for point in results.points:
        payload = point.payload or {}
        details = payload.get("details") or {}
        searchable_text = " ".join(
            [
                payload.get("title") or "",
                payload.get("company") or "",
                details.get("description") or "",
            ]
        ).lower()

        matched_keywords = [
            keyword for keyword in keywords if _keyword_found(keyword.lower(), searchable_text)
        ]
        keyword_boost = min(len(matched_keywords) * boost_amount, max_boost)
        boosted_score = point.score + keyword_boost

        boosted_results.append(
            {
                "score": point.score,
                "boosted_score": boosted_score,
                "matched_keywords": matched_keywords,
                "payload": payload,
            }
        )

    return sorted(
        boosted_results,
        key=lambda result: result["boosted_score"],
        reverse=True,
    )[:limit]

def json_serializer(obj):
    if hasattr(obj, "tolist"):
            return obj.tolist()
    if hasattr(obj, "item"):
        return obj.item()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")