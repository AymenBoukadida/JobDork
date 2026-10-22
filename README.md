# JobScout Dorks

A tool for job hunting with Google search operators. You enter roles, skills, location, and a few filters, and it builds copy-paste queries for job boards, ATS career sites, remote boards, and niche sites. The focus is on company career pages and ATS platforms, where postings show up before the big job boards index them.

## Running it

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
uvicorn app.main:app --reload
```


## Catching postings before the boards do

Companies publish a job on their own careers page or ATS-hosted board first. Aggregators like LinkedIn and Indeed re-index it hours or days later. The app targets that gap in three ways:

1. The ATS Platforms section queries each backend directly. 17 backends are covered, from Greenhouse and Lever to Workday, Workable, Teamtailor, Taleo, and UKG. Pair these queries with the posted-within filter.
2. The Company career sites field takes domains like `stripe.com, photoroom.com` and builds one query per site plus a combined one.
3. The Target company field adds two queries: the company's own site with job boards subtracted, and a lookup for the company across hosted ATS boards, which finds the company's board even when you don't know its domain.

The Career pages only query does the same subtraction web-wide: it removes LinkedIn, Indeed, Glassdoor, ZipRecruiter, and other aggregators so results stay on employer-owned pages.

Note that Google's `after:` filter uses the date Google indexed a page, not the real posting date, so treat it as approximate.

## What it generates

| Category | Examples |
|----------|----------|
| Job Boards | LinkedIn, Indeed, Glassdoor, ZipRecruiter |
| Tunisia Job Boards | TanitJobs, Option Carrière TN, Keejob (when location is Tunisia or preset is active) |
| ATS Platforms | Greenhouse, Lever, Ashby, Workday, Workable, Eightfold, Teamtailor, Taleo, iCIMS, UKG |
| Remote Boards | We Work Remotely, Remote OK, Remotive |
| Company Direct | Career pages without board noise, hiring announcements, per-domain queries, ATS board lookup |
| Tech & Dev | Authentic Jobs, Arc.dev, HN "Who's Hiring" |
| Domain Niche | Sector-specific boards (when a preset is active) |
| Advanced | Salary mentions, no-recruiter filters |

Other features: multiple titles combined with OR or AND, time filtering via `after:YYYY-MM-DD`, domain presets (cybersecurity, data, devops, Tunisia, and more) with pre-filled titles and niche boards, CV upload parsed in memory to pre-fill the form, and search history kept in your browser.

## API

Generate dorks:

```bash
curl -X POST http://127.0.0.1:8000/api/dorks \
  -H "Content-Type: application/json" \
  -d '{
    "titles": ["Software Engineer", "Backend Developer"],
    "title_mode": "or",
    "location": "London",
    "skills": ["Python"],
    "time_filter": "30d",
    "preset_id": "cybersecurity",
    "company_domains": ["stripe.com", "monzo.com"]
  }'
```

Other endpoints:

```bash
curl http://127.0.0.1:8000/api/presets
curl http://127.0.0.1:8000/api/time-filters
curl http://127.0.0.1:8000/api/ats-platforms
curl -X POST http://127.0.0.1:8000/api/cv/parse -F "cv=@resume.pdf"
```

## Tips

- Open the generated links in an incognito window for less personalized results.
- The tool only builds queries. It does not scrape Google or any site.
- Query length is capped and long queries get trimmed before they reach Google.
