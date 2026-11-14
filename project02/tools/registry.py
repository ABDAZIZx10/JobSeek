import json
import inspect
from tools.profile_tool import get_cv_profile, update_cv_profile
from tools.data_tool import get_job_stats
from tools.search_tool import search_jobs
from tools.tailor_tool import match_all_jobs, tailor_cv
from tools.scraper_tool import scrape_jobs

# 1. JSON Schemas for Groq function calling
TOOL_SCHEMAS = [
    {
        "type":"function",
        "function":{
            "name":"update_cv_profile",
            "description": "Add or correct fields in the user's CV profile when the user states them in chat (e.g. seniority, years of experience, extra skills). Only pass the fields the user mentioned. Run match_all_jobs again afterwards.",
            "parameters": {
                "type": "object",
                "properties": {
                    "seniority": {
                        "type": "string",
                        "enum": ["entry level", "junior", "mid", "mid-senior level", "senior", "lead", "manager", "director"],
                        "description": "The user's seniority level"
                    },
                    "experience_years": {
                        "type": "number",
                        "description": "Total years of professional experience"
                    },
                    "skills": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Skills to add to the profile"
                    },
                    "target_roles": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Job titles the user is targeting"
                    },
                    "certifications": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Certifications to add"
                    }
                },
            "required": []
            },
            
        }
    }
    ,{
        "type": "function",
        "function": {
            "name": "get_job_stats",
            "description": "Check if the database has jobs and returns the total count. Always call this first before searching or matching if you are unsure of data availability.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_jobs",
            "description": "Search the job database using semantic similarity. Best for broad searches like 'Python developer in London'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query or job title to look for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of results to return (default 5)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "match_all_jobs",
            "description": "Matches all jobs in the database against the user's CV profile using multi-factor scoring (skills, experience, seniority). Saves matches in memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Number of top matching jobs to return (default 5)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "tailor_cv",
            "description": "Generates tailored recommendations for top jobs. NOTE: Requires match_all_jobs to have been run first.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {
                        "type": "integer",
                        "description": "Number of top matches to tailor for (default 3)"
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_jobs",
            "description": "Scrapes fresh LinkedIn jobs and embeds them. Pass short role keywords and an optional location from the user request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keywords": {
                        "type": "string",
                        "description": "Short LinkedIn search keywords, e.g. 'junior python developer'"
                    },
                    "location": {
                        "type": "string",
                        "description": "Job location, e.g. 'United States' or 'London'"
                    }
                },
                "required": ["keywords"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cv_profile",
            "description": "this tool allows you to get information about the cv the user has uploaded if it exists and the user has uploaded it else it will return an error and will prompt the user to upload his cv instead",
            "parameters": {
                "type": "object",
                "properties": {                    
                },
                "required": []
            }
        }
    }
]

# 2. Registry Engine
class ToolRegistry:
    def __init__(self):
        self.state = {
            "last_matches": [],
            "last_search_results": [],
            "cv_text": None,
            "cv_profile": None,
            "cv_overrides": {}
        }
        self.tools = {
            "get_job_stats": get_job_stats,
            "search_jobs": search_jobs,
            "match_all_jobs": match_all_jobs,
            "tailor_cv": tailor_cv,
            "scrape_jobs": scrape_jobs,
            "update_cv_profile": update_cv_profile,
            "get_cv_profile": get_cv_profile
        }

    def get_schemas(self):
        """Returns the list of tool schemas for Groq."""
        return TOOL_SCHEMAS

    def execute(self, name: str, args: dict) -> str:
        """Executes the tool by name with arguments and returns a JSON string."""
        if name not in self.tools:
            return json.dumps({"status": "error", "message": f"Tool '{name}' not found."})

        func = self.tools[name]
        try:
            # Inject shared state if the tool accepts 'state'
            sig = inspect.signature(func)
            if "state" in sig.parameters:
                args["state"] = self.state

            result = func(**args)
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"status": "error", "message": f"Execution error in '{name}': {str(e)}"})
