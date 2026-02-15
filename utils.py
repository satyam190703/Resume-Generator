import os
import json
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def build_prompt(user_data, job_desc):
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
        f"- {e.get('degree')} from {e.get('institution')} ({e.get('year')}) with score {e.get('score')}"
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
You are a professional resume writer and grammar fixer for ATS-friendly resumes.

Using the following user profile and job description, generate:
1. A short 3-line professional summary
2. A list of 8–10 job-relevant skills
3. 2 project entries with title + 2-line description
4. Suggestions for improving resume quality (email, LinkedIn, project titles, etc.)

Only respond with JSON in this format:
{{
  "summary": "...",
  "skills": ["...", "..."],
  "projects": [
    {{"title": "...", "desc": "..."}},
    {{"title": "...", "desc": "..."}}
  ],
  "suggestions": ["...", "..."]
}}

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
"""


def generate_resume_data(user_data, job_desc):
    prompt = build_prompt(user_data, job_desc)

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You're an expert in resume building and ATS optimization."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192"
        )

        content = chat_completion.choices[0].message.content
        json_start = content.index("{")
        json_end = content.rindex("}") + 1
        parsed = json.loads(content[json_start:json_end])

        return {
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "phone": user_data.get("phone"),
            "location": user_data.get("location", ""),
            "linkedin": user_data.get("linkedin", ""),
            "github": user_data.get("github", ""),
            "summary": parsed.get("summary", ""),
            "skills": parsed.get("skills", []),
            "projects": parsed.get("projects", []),
            "education": user_data.get("education", []),
            "internships": user_data.get("internships", []),
            "achievements": user_data.get("achievements", []),
            "responsibilities": user_data.get("responsibilities", []),
            "extra_activities": user_data.get("extra_activities", []),
            "suggestions": parsed.get("suggestions", [])
        }

    except Exception as e:
        print("⚠️ Error from Groq or JSON parsing failed:", e)
        return {
            "name": user_data.get("name"),
            "email": user_data.get("email"),
            "phone": user_data.get("phone"),
            "location": user_data.get("location", ""),
            "linkedin": user_data.get("linkedin", ""),
            "github": user_data.get("github", ""),
            "summary": "Enthusiastic and quick learner seeking opportunities to grow.",
            "skills": ["Problem Solving", "Teamwork", "Python", "Communication"],
            "projects": [],
            "education": user_data.get("education", []),
            "internships": user_data.get("internships", []),
            "achievements": user_data.get("achievements", []),
            "responsibilities": user_data.get("responsibilities", []),
            "extra_activities": user_data.get("extra_activities", []),
            "suggestions": ["AI enhancement failed. Fallback data used."]
        }


def analyze_email_with_groq(email, name):
    prompt = f"""
    Analyze the email address: {email}
    - Is it professional enough to be used in a resume?
    - If not, suggest a better alternative using the name: "{name}" (e.g., first.last@example.com).
    - Explain briefly why it's not appropriate.

    Respond strictly in this JSON format:
    {{
        "is_professional": true/false,
        "suggested_email": "example@example.com",
        "reason": "short explanation here"
    }}
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You're an expert in resume building and ATS optimization."},
                {"role": "user", "content": prompt}
            ],
            model="mixtral-8x7b-32768"
        )
        response_content = chat_completion.choices[0].message.content
        return json.loads(response_content)
    except Exception as e:
        return {
            "is_professional": True,
            "suggested_email": email,
            "reason": "Fallback: could not analyze email."
        }
