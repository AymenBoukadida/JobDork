from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NicheBoard:
    name: str
    site_filter: str
    description: str


@dataclass(frozen=True)
class DomainPreset:
    id: str
    name: str
    description: str
    icon: str
    titles: tuple[str, ...]
    skills: tuple[str, ...]
    exclude_terms: tuple[str, ...]
    niche_boards: tuple[NicheBoard, ...]


DOMAIN_PRESETS: tuple[DomainPreset, ...] = (
    DomainPreset(
        "cybersecurity",
        "Cybersecurity",
        "SOC, AppSec, and GRC roles on infosec-focused boards",
        "🛡️",
        (
            "Security Engineer",
            "SOC Analyst",
            "Penetration Tester",
            "Cybersecurity Analyst",
        ),
        ("SIEM", "Splunk", "AWS", "ISO 27001", "Incident Response"),
        ("intern", "training course"),
        (
            NicheBoard(
                "InfoSec Jobs",
                "site:infosec-jobs.com OR site:infosecjobs.com",
                "Dedicated information-security job boards",
            ),
            NicheBoard(
                "CyberSec Listings",
                'site:cybersecurityjobsite.com OR inurl:cybersecurity jobs "apply"',
                "Cybersecurity niche boards and career pages",
            ),
            NicheBoard(
                "Clearance / Gov",
                "site:clearedjobs.net OR (site:usajobs.gov cybersecurity)",
                "Clearance and public-sector security roles",
            ),
        ),
    ),
    DomainPreset(
        "data",
        "Data & Analytics",
        "Data science, analytics, and ML engineering roles",
        "📊",
        ("Data Scientist", "Data Analyst", "Data Engineer", "ML Engineer"),
        ("Python", "SQL", "Spark", "Tableau", "Machine Learning"),
        ("bootcamp", "certificate program"),
        (
            NicheBoard(
                "Kaggle Jobs",
                'site:kaggle.com jobs OR site:kaggle.com/discussions "hiring"',
                "Kaggle community job threads",
            ),
            NicheBoard(
                "AI / ML Boards",
                "site:mljobs.com OR site:ai-jobs.net",
                "Machine-learning focused listings",
            ),
        ),
    ),
    DomainPreset(
        "devops",
        "DevOps & Platform",
        "SRE, platform, and cloud infrastructure roles",
        "⚙️",
        (
            "DevOps Engineer",
            "Site Reliability Engineer",
            "Platform Engineer",
            "Cloud Engineer",
        ),
        ("Kubernetes", "Terraform", "AWS", "Docker", "CI/CD"),
        ("course", "certification only"),
        (
            NicheBoard(
                "DevOps Jobs",
                'inurl:devops jobs "apply" OR site:devopsjobs.io',
                "DevOps-specific job sources",
            ),
        ),
    ),
    DomainPreset(
        "frontend",
        "Frontend & UI",
        "React, design systems, and product UI engineering",
        "🎨",
        ("Frontend Developer", "UI Engineer", "React Developer", "Web Developer"),
        ("React", "TypeScript", "CSS", "Next.js", "Figma"),
        ("tutorial", "bootcamp"),
        (
            NicheBoard(
                "Frontend Focus",
                'site:frontenddeveloperjob.com OR inurl:frontend jobs "apply"',
                "Frontend-specific job boards",
            ),
        ),
    ),
    DomainPreset(
        "product",
        "Product & PM",
        "Product management and product operations",
        "📦",
        ("Product Manager", "Product Owner", "Technical Product Manager"),
        ("Agile", "Roadmap", "SQL", "Jira", "Stakeholder"),
        ("certification", "course"),
        (
            NicheBoard(
                "Product Jobs",
                "site:productjobs.com OR site:mindtheproduct.com jobs",
                "Product-management job sources",
            ),
        ),
    ),
    DomainPreset(
        "healthcare",
        "Healthcare & Life Sciences",
        "Clinical informatics, biotech, and health-tech roles",
        "🏥",
        (
            "Clinical Informatics Specialist",
            "Bioinformatics Engineer",
            "Health Data Analyst",
        ),
        ("HIPAA", "EHR", "HL7", "Python", "Clinical Trials"),
        ("volunteer", "unpaid"),
        (
            NicheBoard(
                "BioTech Jobs",
                "site:biohealthmatics.com jobs OR site:biotech.org careers",
                "Life-sciences and biotech career pages",
            ),
        ),
    ),
    DomainPreset(
        "finance",
        "Finance & FinTech",
        "Accounting, FP&A, and financial technology roles",
        "💰",
        ("Financial Analyst", "Accountant", "FinTech Engineer", "Quantitative Analyst"),
        ("Excel", "SQL", "Python", "Financial Modeling", "Bloomberg"),
        ("unpaid internship", "training course"),
        (
            NicheBoard(
                "eFinancialCareers",
                "site:efinancialcareers.com",
                "Finance and banking job board",
            ),
            NicheBoard(
                "FinTech Jobs",
                'inurl:fintech jobs "apply" OR site:fintechfutures.com jobs',
                "FinTech-focused listings",
            ),
        ),
    ),
    DomainPreset(
        "legal",
        "Legal & Compliance",
        "In-house counsel, paralegal, and compliance roles",
        "⚖️",
        ("Legal Counsel", "Paralegal", "Compliance Officer", "Contract Manager"),
        ("GDPR", "Contract Law", "Regulatory", "Due Diligence"),
        ("volunteer", "pro bono only"),
        (
            NicheBoard(
                "Legal Jobs",
                "site:lawcrossing.com OR site:legalweekjobs.com",
                "Legal profession job boards",
            ),
        ),
    ),
    DomainPreset(
        "sysadmin",
        "Sysadmin & Infrastructure",
        "Linux/Windows servers, virtualization, and on-prem or hybrid IT ops",
        "🖥️",
        (
            "Systems Administrator",
            "System Administrator",
            "Linux Administrator",
            "Windows Administrator",
            "Infrastructure Engineer",
            "IT Systems Engineer",
        ),
        ("Linux", "Windows Server", "Active Directory", "VMware", "PowerShell", "Bash"),
        ("intern", "course only"),
        (
            NicheBoard(
                "Sysadmin Listings",
                'intitle:"systems administrator" OR intitle:"system administrator" (apply OR hiring)',
                "Pages titled for sysadmin roles",
            ),
            NicheBoard(
                "Linux / Unix Ops",
                '("Linux Administrator" OR "Unix Administrator") (apply OR opening) -tutorial',
                "Linux-focused administration postings",
            ),
            NicheBoard(
                "Gov IT / Clearance",
                'site:usajobs.gov ("IT Specialist" OR "Systems Administrator")',
                "US public-sector IT and sysadmin roles",
            ),
        ),
    ),
    DomainPreset(
        "it_support",
        "IT Support & Helpdesk",
        "Service desk, desktop support, and end-user IT roles",
        "🎧",
        (
            "IT Support Specialist",
            "Help Desk Technician",
            "Desktop Support Engineer",
            "Service Desk Analyst",
            "Technical Support Engineer",
        ),
        ("Active Directory", "Ticketing", "Windows", "Office 365", "Troubleshooting"),
        ("volunteer", "unpaid"),
        (
            NicheBoard(
                "Helpdesk Jobs",
                '(intitle:"help desk" OR intitle:"service desk") (apply OR hiring) -course',
                "Help desk and service desk openings",
            ),
            NicheBoard(
                "Desktop Support",
                'intitle:"desktop support" (apply OR opening OR "we are hiring")',
                "Desktop and endpoint support roles",
            ),
        ),
    ),
    DomainPreset(
        "network",
        "Network Engineering",
        "Routing, switching, firewalls, and enterprise networking",
        "🌐",
        (
            "Network Engineer",
            "Network Administrator",
            "Network Operations Engineer",
            "NOC Engineer",
        ),
        ("Cisco", "BGP", "Firewall", "VPN", "TCP/IP", "LAN/WAN"),
        ("certification only", "training"),
        (
            NicheBoard(
                "Network Jobs",
                '(intitle:"network engineer" OR intitle:"network administrator") (apply OR hiring)',
                "Network engineering job postings",
            ),
            NicheBoard(
                "NOC Roles",
                'intitle:"NOC" (engineer OR analyst OR technician) (apply OR opening)',
                "Network operations center positions",
            ),
        ),
    ),
    DomainPreset(
        "cloud_it",
        "Cloud & M365 IT",
        "Azure, AWS, Microsoft 365, and cloud systems administration",
        "☁️",
        (
            "Cloud Administrator",
            "Azure Administrator",
            "AWS Cloud Engineer",
            "Microsoft 365 Administrator",
            "Cloud Systems Engineer",
        ),
        ("Azure", "AWS", "Microsoft 365", "Entra ID", "Terraform", "CloudFormation"),
        ("bootcamp", "exam prep"),
        (
            NicheBoard(
                "Azure / M365 Admin",
                '("Azure Administrator" OR "Microsoft 365 Administrator") (apply OR hiring)',
                "Microsoft cloud administration roles",
            ),
            NicheBoard(
                "AWS Cloud Ops",
                '("AWS Administrator" OR "Cloud Engineer") site:*.amazon.com careers OR (apply AWS admin)',
                "AWS-focused cloud operations listings",
            ),
        ),
    ),
    DomainPreset(
        "it_general",
        "General IT",
        "Broad IT specialist, analyst, and operations roles across industries",
        "💼",
        (
            "IT Specialist",
            "IT Analyst",
            "IT Operations Engineer",
            "Information Technology Manager",
            "IT Generalist",
        ),
        ("ITIL", "Active Directory", "Networking", "Scripting", "Documentation"),
        ("internship unpaid", "volunteer"),
        (
            NicheBoard(
                "IT Specialist",
                'intitle:"IT Specialist" OR intitle:"Information Technology" (apply OR opening)',
                "General IT specialist postings",
            ),
            NicheBoard(
                "IT Job Boards UK/EU",
                "site:technojobs.co.uk OR site:itjobswatch.co.uk",
                "Regional IT-focused job boards",
            ),
            NicheBoard(
                "MSP / Managed Services",
                '("managed service" OR MSP) ("systems engineer" OR "IT engineer") (hiring OR apply)',
                "Managed service provider IT roles",
            ),
        ),
    ),
    DomainPreset(
        "backend",
        "Backend & API",
        "Server-side development, APIs, and distributed systems",
        "🧱",
        (
            "Backend Developer",
            "Backend Engineer",
            "API Developer",
            "Java Developer",
            "Go Developer",
        ),
        ("Python", "Java", "Go", "PostgreSQL", "REST", "Microservices"),
        ("tutorial", "bootcamp"),
        (
            NicheBoard(
                "Backend Listings",
                'intitle:"backend" (developer OR engineer) (apply OR hiring) -course',
                "Backend engineering job postings",
            ),
        ),
    ),
    DomainPreset(
        "mobile",
        "Mobile Development",
        "iOS, Android, and cross-platform mobile engineering",
        "📱",
        (
            "Mobile Developer",
            "iOS Developer",
            "Android Developer",
            "React Native Developer",
            "Flutter Developer",
        ),
        ("Swift", "Kotlin", "React Native", "Flutter", "Mobile UI"),
        ("bootcamp", "tutorial"),
        (
            NicheBoard(
                "Mobile Jobs",
                '(intitle:"mobile developer" OR intitle:"iOS developer" OR intitle:"Android developer") apply',
                "Mobile development openings",
            ),
        ),
    ),
    DomainPreset(
        "tunisia",
        "Tunisia",
        "French/Arabic market roles on local boards and .tn career pages",
        "🇹🇳",
        (
            "Ingénieur",
            "Développeur",
            "Technicien informatique",
            "Consultant",
        ),
        ("Java", "PHP", "SQL", "Anglais", "Réseau"),
        ("stage", "formation", "PFE"),
        (
            NicheBoard(
                "LinkedIn (Tunisia)",
                "site:linkedin.com/jobs/view (Tunisia OR Tunis OR Sousse OR Sfax)",
                "LinkedIn jobs mentioning Tunisian cities or country",
            ),
            NicheBoard(
                "Tunisian .tn Sites",
                'site:.tn (emploi OR recrutement OR "offre d\'emploi" OR carrières)',
                "Career pages on Tunisian domains",
            ),
            NicheBoard(
                "TanitJobs + Option Carrière",
                "site:tanitjobs.com OR site:optioncarriere.tn",
                "Combined search on top local boards",
            ),
        ),
    ),
)

PRESET_BY_ID = {p.id: p for p in DOMAIN_PRESETS}


def list_domain_presets() -> list[dict]:
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "icon": p.icon,
            "titles": list(p.titles),
            "skills": list(p.skills),
            "exclude_terms": list(p.exclude_terms),
        }
        for p in DOMAIN_PRESETS
    ]


def get_domain_preset(preset_id: str) -> DomainPreset:
    if preset_id not in PRESET_BY_ID:
        raise ValueError(f"Unknown domain preset: {preset_id}")
    return PRESET_BY_ID[preset_id]
