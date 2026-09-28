from tools.data_tool import get_job_stats
from tools.search_tool import search_jobs
from tools.tailor_tool import match_all_jobs, tailor_cv

print(get_job_stats())
print(search_jobs("python developer", limit=3))

state = {"cv_text": open("path/to/cv.txt", encoding="utf-8").read(),
         "cv_profile": None, "last_matches": []}
print(match_all_jobs(limit=3, state=state))
print(tailor_cv(top_n=1, state=state))