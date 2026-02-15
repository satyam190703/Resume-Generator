import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def build_prompt(user_data, job_desc):
    # Extract user info
    name = user_data.get("name", "")
    location = user_data.get("location", "")
    phone = user_data.get("phone", "")
    linkedin = user_data.get("linkedin", "")
    github = user_data.get("github", "")
    education = user_data.get("education", [])
    internships = user_data.get("internships", [])
    achievements = user_data.get("achievements", [])
    responsibilities = user_data.get("responsibilities", [])
    extra_activities = user_data.get("extra_activities", [])

    edu_block = "\n".join(
        f"- {e.get('degree')} from {e.get('institution')} ({e.get('year')}) with {e.get('score')} marks"
        for e in education
    )

    intern_block = "\n".join(
        f"- {i.get('title')} at {i.get('company')} in {i.get('field')}:\n  {i.get('desc')}"
        for i in internships
    )

    ach_block = "\n".join(f"- {a}" for a in achievements)
    res_block = "\n".join(f"- {r}" for r in responsibilities)
    act_block = "\n".join(f"- {a}" for a in extra_activities)

    return f"""
Given the following user profile and job description, generate a resume with:

1. A 3-line professional summary.
2. A list of 8–10 skills tailored to the job.
3. Two projects with title and description (each in max 3 lines), aligned with the job description.

User Profile:
Name: {name}
Phone: {phone}
Location: {location}
LinkedIn: {linkedin}
GitHub: {github}

Education:
{edu_block}

Internships:
{intern_block}

Achievements:
{ach_block}

Responsibilities:
{res_block}

Extra Activities:
{act_block}

Job Description:
{job_desc}

Respond ONLY with JSON in this format:
{{
  "summary": "...",
  "skills": ["...", "..."],
  "projects": [
    {{"title": "...", "desc": "..."}},
    {{"title": "...", "desc": "..."}}
  ]
}}
"""


def call_groq_api(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {os.getenv('GROQ_API_KEY')}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a professional resume writer."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }

    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # Try to extract JSON from content
        json_str = content[content.index("{"):content.rindex("}") + 1]
        return json.loads(json_str)

    except Exception as e:
        print("⚠️ Error from Groq or JSON parsing failed:", e)
        return None


def generate_resume_data(user_data, job_description):
    prompt = build_prompt(user_data, job_description)
    ai_response = call_groq_api(prompt)

    if ai_response:
        return {
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "phone": user_data.get("phone"),
            "location": user_data.get("location", ""),
            "linkedin": user_data.get("linkedin", ""),
            "github": user_data.get("github", ""),
            "summary": ai_response.get("summary", ""),
            "skills": ai_response.get("skills", []),
            "projects": ai_response.get("projects", []),
            "education": user_data.get("education", []),
            "internships": user_data.get("internships", []),
            "achievements": user_data.get("achievements", []),
            "responsibilities": user_data.get("responsibilities", []),
            "extra_activities": user_data.get("extra_activities", [])
        }

    # Fallback if AI fails
    return {
        "name": user_data.get("name"),
        "email": user_data.get("email"),
        "phone": user_data.get("phone"),
        "location": user_data.get("location", ""),
        "linkedin": user_data.get("linkedin", ""),
        "github": user_data.get("github", ""),
        "summary": "Enthusiastic and adaptive learner looking to contribute skills and grow in a professional environment.",
        "skills": ["Teamwork", "Communication", "Problem Solving"],
        "projects": [],
        "education": user_data.get("education", []),
        "internships": user_data.get("internships", []),
        "achievements": user_data.get("achievements", []),
        "responsibilities": user_data.get("responsibilities", []),
        "extra_activities": user_data.get("extra_activities", [])
    }
