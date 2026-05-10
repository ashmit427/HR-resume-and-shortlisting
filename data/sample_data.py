SAMPLE_JD = """
Job Title: Senior Software Engineer — Backend Systems
Company: TechCorp India Pvt. Ltd.
Location: Bengaluru / Hybrid

About the Role:
We are looking for a Senior Backend Engineer to join our payments infrastructure team.
You will design, build, and own highly available distributed systems that process millions
of transactions daily.

Required Skills:
- Python (5+ years) with production experience
- Distributed systems (Kafka, RabbitMQ, or similar)
- PostgreSQL or equivalent relational DB (query optimization, indexing)
- REST API design and microservices architecture
- Docker and Kubernetes for container orchestration
- Strong problem-solving and system design skills

Preferred Skills:
- Redis for caching
- AWS or GCP cloud services
- Go language
- Experience with payments or fintech domain
- OpenTelemetry or distributed tracing

Experience: 4–7 years in software engineering
Education: B.Tech/BE in Computer Science or equivalent
Certifications: AWS/GCP certification is a plus

Key Responsibilities:
- Design and implement scalable backend services for payment processing
- Lead code reviews and mentor junior engineers
- Participate in on-call rotation and ensure 99.99% uptime
- Collaborate with product and data teams on new features
- Write technical design documents and architecture proposals
"""

SAMPLE_RESUMES = {
    "priya_sharma.txt": """
Priya Sharma
priya.sharma@email.com | +91-9876543210 | LinkedIn: linkedin.com/in/priyasharma

PROFESSIONAL SUMMARY
Senior software engineer with 6 years of experience building scalable backend systems
in Python. Led migration of monolithic architecture to microservices at FinPay, reducing
latency by 40%. Passionate about distributed systems and high-throughput pipelines.

EXPERIENCE

Senior Software Engineer | FinPay Technologies | Jan 2021 – Present (3.5 yrs)
- Designed and owned Kafka-based event streaming pipeline processing 2M+ events/day
- Led team of 4 engineers to rebuild payment settlement service (Python, PostgreSQL)
- Reduced P99 latency from 800ms to 120ms through query optimization and Redis caching
- Implemented Kubernetes-based auto-scaling reducing infra costs by 35%
- Mentored 3 junior engineers; conducted 50+ code reviews per quarter

Software Engineer | Infosys Ltd | Jun 2018 – Dec 2020 (2.5 yrs)
- Built REST APIs for banking portal serving 500K daily active users
- Migrated legacy Oracle DB to PostgreSQL with zero downtime
- Implemented JWT-based auth service in Python/FastAPI

EDUCATION
B.Tech Computer Science | BITS Pilani | 2018 | GPA: 8.7/10

CERTIFICATIONS
- AWS Certified Solutions Architect – Associate (2022)
- Certified Kubernetes Administrator (CKA) – 2023

SKILLS
Python, FastAPI, Django, Kafka, PostgreSQL, Redis, Docker, Kubernetes, AWS (EC2, RDS, SQS),
REST APIs, Microservices, Git, Linux, System Design, Go (learning)

PROJECTS
1. Open-source: pyflow-async — async task orchestration library (GitHub: 1.2k stars)
2. Internal: Real-time fraud detection pipeline using Kafka Streams + ML scoring
3. Personal: Distributed key-value store implementation in Python (learning project)
""",

    "rahul_verma.txt": """
Rahul Verma
rahulv@gmail.com | 8765432109

SUMMARY
Enthusiastic software developer with 2 years of experience. Quick learner,
team player, good communication skills. Looking for growth opportunities.

WORK EXPERIENCE
Software Developer | StartupXYZ | 2022-2024
- Worked on backend development using Python and Django
- Fixed bugs and added features to existing codebase
- Participated in daily standups

Intern | TechSolutions | 2021-2022
- Helped with database queries
- Assisted senior developers

EDUCATION
B.Tech IT | Rajasthan Technical University | 2022

SKILLS
Python, Django, MySQL, HTML, CSS, JavaScript, Git

PROJECTS
- Todo App using Django
- College Management System (final year project)

HOBBIES
Cricket, Reading, Coding
""",

    "ananya_krishnan.txt": """
Ananya Krishnan
ananya.k@protonmail.com | +91-7654321098

PROFESSIONAL PROFILE
Backend engineer with 5 years building fintech and payments infrastructure.
Strong in distributed systems and database engineering. Ex-PhonePe, Ex-Razorpay.

EXPERIENCE

Software Engineer II | Razorpay | Mar 2022 – Present
- Built webhook delivery system handling 500K+ callbacks/day with 99.95% delivery rate
- Designed idempotency layer for payment APIs preventing duplicate charges
- Tech stack: Python, Go, Kafka, PostgreSQL, Redis, GCP

Software Engineer | PhonePe | Aug 2019 – Feb 2022
- Core payments team: UPI transaction processing pipeline
- Implemented circuit breaker pattern reducing cascading failures by 70%
- Performance: reduced DB query time by 60% via proper indexing strategy

EDUCATION
M.Tech Computer Science | NIT Trichy | 2019

CERTIFICATIONS
- Google Cloud Professional Developer (2023)
- MongoDB Certified Developer

TECHNICAL SKILLS
Python, Go, Kafka, RabbitMQ, PostgreSQL, MySQL, Redis, GCP, Docker,
Kubernetes, gRPC, REST, Microservices, System Design, Distributed Systems

KEY PROJECTS
1. Webhook delivery system: Built from scratch, 99.95% SLA, 500K+ daily events
2. UPI Autopay engine: Handles scheduled payment mandates for 10M+ users
3. Chaos engineering framework: Internal tool for reliability testing

PUBLICATIONS
- "Designing Idempotent APIs at Scale" — Medium Engineering Blog (2023)
""",

    "vikram_nair.txt": """
Vikram Nair | vikram.nair@outlook.com

10 Years of Experience | Full Stack / Backend

I am an experienced developer having worked in multiple companies. I know Python,
Java, PHP, JavaScript, MySQL, MongoDB and many other technologies. Good at
solving problems and working in teams.

Experience:
TechFirm A (2020-2024) - Senior Developer
Various projects. Led a team. Used Python sometimes.

TechFirm B (2017-2020) - Developer
Web development. PHP and Python projects.

StartupC (2014-2017) - Junior Dev
Learning phase.

Education: BCA 2014

Skills: Python, Java, PHP, SQL, Linux, some cloud stuff

References available on request.
""",

    "meera_pillai.txt": """
Meera Pillai
meera.pillai@techmail.com | Bengaluru

SENIOR ENGINEER | 5 Years | Distributed Systems Specialist

ABOUT ME
I architect and implement large-scale distributed backends. Former SDE-II at Amazon.
I wrote and published a technical guide on Kafka consumer group management that reached
50K+ engineers on Medium. I thrive in high-ownership, zero-hand-holding environments.

EXPERIENCE

SDE-II | Amazon (AWS Team) | 2021 – 2024 (3 yrs)
- Owned SQS dead-letter queue monitoring service (Python, 8 AWS regions)
- Designed cross-region replication protocol; filed 1 internal patent application
- Handled on-call for services with 99.999% SLA requirements

Software Engineer | Flipkart | 2019 – 2021
- Kafka-based order pipeline: 1M+ orders/day processed with <50ms P99 latency
- Python microservices architecture; contributed to shared platform libraries

EDUCATION
B.Tech CSE | PSG College of Technology | 2019

AWS Certifications: Solutions Architect Professional + Developer Associate (2022)

SKILLS
Python, Java, Kafka, SQS/SNS, DynamoDB, PostgreSQL, Redis, Docker,
Kubernetes, AWS, Terraform, System Design, Distributed Systems

PROJECTS
1. Kafka consumer group auto-rebalancer (open source, 800 GitHub stars)
2. Internal: Multi-region failover orchestration for AWS S3 lifecycle events
3. Published: "Kafka at scale: lessons from 3 years in production" (Medium, 50K reads)
"""
}
