"""
section_parser.py
Splits a resume into named sections (skills, experience, projects, etc.).
Handles both newline-based headings and inline "Section: content" formats.
"""
import re
from .constants import SECTION_PATTERNS


def split_into_sections(text: str) -> dict:
    """
    Split resume text into a dict of {section_name: section_text}.

    Detection strategy (in order):
      1. Newline-based headings — a short line (<80 chars) matching a section pattern.
      2. Inline colon headings — "Skills: React, Node.js …"
      3. Fallback — if no sections are detected, every section key maps to the full text
         so that scoring still works even for unstructured resumes.
    """
    # Pass 1: line-by-line scan for heading lines
    lines = text.split('\n')
    sections: dict = {}
    current = 'summary'
    buffer: list = []

    for line in lines:
        stripped = line.strip()
        matched = None
        for sec, pattern in SECTION_PATTERNS.items():
            if pattern.search(stripped) and len(stripped) < 80:
                matched = sec
                break
        if matched:
            if buffer:
                sections[current] = sections.get(current, '') + '\n' + '\n'.join(buffer)
            current = matched
            buffer = []
        else:
            buffer.append(line)

    if buffer:
        sections[current] = sections.get(current, '') + '\n' + '\n'.join(buffer)

    # Pass 2: inline "Section: …" patterns for anything not yet found
    for sec, pattern in SECTION_PATTERNS.items():
        if sec not in sections or not sections[sec].strip():
            m = re.search(
                r'(?:^|\n)' + pattern.pattern + r'\s*[:\-]\s*(.+?)(?=\n[A-Z]|$)',
                text, re.I | re.S
            )
            if m:
                sections[sec] = m.group(m.lastindex)

    # Fallback: unstructured resume → broadcast full text to every section
    detected = [s for s in sections if sections[s].strip() and s != 'summary']
    if not detected:
        for sec in ['skills', 'experience', 'projects', 'education', 'certifications']:
            sections[sec] = text

    return sections
