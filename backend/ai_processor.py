"""
ai_processor.py — Promise vs Progress
======================================
Uses Google Gemini API to:
1. Extract structured data from raw project descriptions
2. Detect project delay status
"""

import os
import json
import re
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai


# ── Setup ─────────────────────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Configure Gemini
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# ── TASK 1: AI Data Structuring ───────────────────────────────────────────────

def extract_structured_data(raw_text: str) -> dict:
    """
    Send raw project text to Gemini and get back structured JSON.
    """
    prompt = f"""
You are a data extraction assistant for a civic-tech project tracking 
Karnataka government road infrastructure projects in India.

Extract structured information from the following raw project text.
Return ONLY a valid JSON object with these exact fields:
- project_name: string (full project name)
- location: string (city or district in Karnataka)
- budget: number (total budget in INR as integer, e.g. 120000000 for 12 crore. null if not found)
- expected_completion: number (year as integer e.g. 2025, null if not found)
- sector: string (always "Road" for this project)

Rules:
- If a field is missing or unclear, use null
- Budget must be a plain integer in INR (convert crore/lakh to full number)
- Return ONLY the JSON object, no explanation, no markdown

Raw text:
{raw_text}
"""
    try:
        response = client.models.generate_content(model="gemini-2.0-flash-lite", contents=prompt)
        raw_response = response.text.strip()

        # Strip markdown code fences if present
        raw = re.sub(r"```json|```", "", raw).strip()

        data = json.loads(raw)

        # Validate and fill missing fields
        return {
            "project_name":        data.get("project_name") or "",
            "location":            data.get("location") or "",
            "budget":              int(data["budget"]) if data.get("budget") else None,
            "expected_completion": int(data["expected_completion"]) if data.get("expected_completion") else None,
            "sector":              data.get("sector") or "Road",
        }

    except json.JSONDecodeError as e:
        log.warning(f"Gemini returned invalid JSON: {e}")
        return _empty_structure()
    except Exception as e:
        log.warning(f"Gemini API error: {e}")
        return _empty_structure()


def _empty_structure() -> dict:
    """Return a blank structure when extraction fails."""
    return {
        "project_name":        "",
        "location":            "",
        "budget":              None,
        "expected_completion": None,
        "sector":              "Road",
    }


# ── TASK 2: Delay Detection ───────────────────────────────────────────────────

def detect_delay(project: dict) -> dict:
    """
    Detect if a project is delayed based on expected_completion year.

    Returns: { "status": "Delayed" | "On Track" | "Unknown" }
    """
    current_year = datetime.now().year
    expected = project.get("expected_completion")

    if not expected:
        return {"status": "Unknown"}
    elif current_year > int(expected):
        return {"status": "Delayed"}
    else:
        return {"status": "On Track"}


# ── TASK 3: Process a single project ─────────────────────────────────────────

def process_project(raw_project: dict) -> dict:
    """
    Takes a raw project dict from the scraper,
    enriches it with AI-extracted fields and delay status.
    """
    description = raw_project.get("description") or raw_project.get("name") or ""

    log.info(f"Processing: {raw_project.get('name', 'Unnamed')[:60]}")

    # Step 1: Extract structured data via Gemini
    structured = extract_structured_data(description)

    # Step 2: Detect delay
    delay = detect_delay(structured)

    # Step 3: Merge everything into one clean object
    return {
        "name":                structured["project_name"] or raw_project.get("name", ""),
        "location":            structured["location"]     or raw_project.get("location", ""),
        "budget":              structured["budget"],
        "expected_completion": structured["expected_completion"],
        "sector":              structured["sector"],
        "status":              delay["status"],
        "description":         description,
        "date":                raw_project.get("date", ""),
        "source":              raw_project.get("source", ""),
        "scraped_at":          raw_project.get("scraped_at", ""),
    }


# ── TASK 3: Process all projects ─────────────────────────────────────────────

def process_all(input_file: str = "projects.json", output_file: str = "projects.json"):
    """
    Load projects.json → process each project through AI → save back to projects.json
    """
    if not os.path.exists(input_file):
        log.error(f"{input_file} not found. Run scraper.py first.")
        return

    with open(input_file, encoding="utf-8") as f:
        raw_projects = json.load(f)

    log.info(f"Processing {len(raw_projects)} projects through Gemini...")

    enhanced = []
    for project in raw_projects:
        try:
            result = process_project(project)
            enhanced.append(result)
            time.sleep(3)
        except Exception as e:
            log.warning(f"Skipping project due to error: {e}")
            enhanced.append(project)  # keep original if processing fails

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(enhanced, f, ensure_ascii=False, indent=2)

    log.info(f"Saved {len(enhanced)} enhanced projects → {output_file}")


# ── Run directly ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    process_all()