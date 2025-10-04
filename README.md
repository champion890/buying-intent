# Lead Scoring Backend API

AI-powered lead scoring system that combines rule-based logic with OpenAI GPT-3.5-Turbo to analyze and score B2B leads based on buying intent.

## Live Deployment

**Base URL:** https://buying-intent.onrender.com

**API Documentation (Swagger):** https://buying-intent.onrender.com/swagger/

**Alternative Documentation (ReDoc):** https://buying-intent.onrender.com/redoc/

---

## Features

- Product/Offer management API
- CSV lead upload with validation
- **Hybrid scoring system (Rule-based + AI)**
- Lead intent classification (High/Medium/Low)
- Results export as CSV
- Comprehensive API documentation (Swagger/ReDoc)
- Unit tests for scoring logic
- Docker support
- Production-ready deployment on Render

---

## Tech Stack

- **Framework:** Django 4.2 + Django REST Framework
- **AI Model:** OpenAI GPT-3.5-Turbo
- **Database:** SQLite (easily switchable to PostgreSQL)
- **Deployment:** Render (with Gunicorn)
- **Documentation:** drf-yasg (Swagger/OpenAPI)
- **Containerization:** Docker + Docker Compose

---

## Hybrid Scoring System - Architecture

This API implements a **two-layer hybrid scoring approach** as per assignment requirements:

### Scoring Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    LEAD INPUT (CSV)                         │
│   name, role, company, industry, location, linkedin_bio     │
└──────────────────────┬──────────────────────────────────────┘
                       │
         ┌─────────────┴──────────────┐
         ▼                            ▼
┌──────────────────┐        ┌──────────────────┐
│  RULE LAYER      │        │   AI LAYER       │
│  (Max 50 pts)    │        │  (Max 50 pts)    │
│                  │        │                  │
│ • Role: +20/+10  │        │ • OpenAI GPT-3.5 │
│ • Industry: +20  │        │ • Intent: H/M/L  │
│ • Complete: +10  │        │ • High = 50 pts  │
│                  │        │ • Medium = 30pts │
│ Objective Rules  │        │ • Low = 10 pts   │
└──────────────────┘        └──────────────────┘
         │                            │
         └─────────────┬──────────────┘
                       ▼
            ┌──────────────────┐
            │  FINAL SCORE     │
            │  Rule + AI       │
            │  (Max 100 pts)   │
            └──────────────────┘
                       │
                       ▼
            ┌──────────────────┐
            │ INTENT LABEL     │
            │ High   (≥70)     │
            │ Medium (≥40)     │
            │ Low    (<40)     │
            └──────────────────┘
```

### Layer 1: Rule-Based Scoring (0-50 points)

Objective, deterministic scoring based on structured data:

| Criterion | Points | Description |
|-----------|--------|-------------|
| **Decision Maker Role** | +20 | CEO, CTO, VP, Director, Founder, Owner |
| **Influencer Role** | +10 | Manager, Lead, Architect, Senior |
| **Exact ICP Match** | +20 | Industry matches ideal use case exactly |
| **Adjacent Industry** | +10 | Industry related to ideal use case |
| **Complete Profile** | +10 | All required fields present |

**Example:**
```
Lead: CEO at B2B SaaS company with complete profile
Rule Score = 20 (CEO) + 20 (B2B SaaS ICP) + 10 (complete) = 50 points
```

### Layer 2: AI Scoring (0-50 points)

Contextual analysis using OpenAI GPT-3.5-Turbo:

**Process:**
1. **Prompt Construction** - Combines lead profile + offer details
2. **Intent Classification** - AI analyzes fit and classifies as High/Medium/Low
3. **Point Mapping:**
   - High Intent: 50 points
   - Medium Intent: 30 points
   - Low Intent: 10 points

**AI Prompt Strategy:**

The AI receives:
- **Lead Profile:** Name, role, company, industry, location, LinkedIn bio
- **Offer Context:** Product name, value propositions, ideal customer profile
- **Evaluation Criteria:** Decision authority, ICP fit, relevant experience

**Sample Prompt:**
```
Analyze this lead's buying intent for our product:

LEAD PROFILE:
- Role: VP of Sales
- Company: TechFlow Inc
- Industry: B2B SaaS
- Bio: 10+ years scaling sales teams in SaaS startups

OUR PRODUCT/OFFER:
- Product: AI Outreach Automation
- Value Props: 24/7 outreach, 6x more meetings
- ICP: B2B SaaS mid-market

Evaluate:
1. Decision-making authority?
2. Industry/company match our ICP?
3. Bio shows relevant pain points?
4. Overall likelihood of interest

Classify: High, Medium, or Low
Format: Intent|Reasoning
```

**Why This Works:**
- AI understands context, not just keywords
- Evaluates soft signals (bio sentiment, experience)
- Considers product-prospect fit holistically

### Final Score Calculation

```python
final_score = rule_score + ai_score  # Max 100

# Intent Classification
if final_score >= 70:
    intent = "High"      # Hot lead - immediate follow-up
elif final_score >= 40:
    intent = "Medium"    # Warm lead - nurture campaign
else:
    intent = "Low"       # Cold lead - long-term nurture
```

**Example Breakdown:**
```json
{
  "name": "Sarah Chen",
  "role": "VP of Sales",
  "company": "DataFlow",
  "intent": "High",
  "score": 90,
  "reasoning": "[Rule: Decision maker role (+20), Exact ICP match (+20), Complete profile (+10)] [AI: VP in B2B SaaS with 10+ years experience. Bio mentions scaling challenges our product solves.]",
  "score_breakdown": {
    "rule_score": 50,
    "ai_score": 50
  }
}
```

---

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd lead-scoring-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv

# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` file:
```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Django Configuration
SECRET_KEY=your-django-secret-key-here
DEBUG=True

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1
```

**Get OpenAI API Key:** https://platform.openai.com/api-keys

### 5. Run Database Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 7. Start Development Server
```bash
python manage.py runserver
```

Server running at: **http://localhost:8000**  
Admin panel: **http://localhost:8000/admin/**  
API docs: **http://localhost:8000/swagger/**

---

## API Usage Examples

### 1. Create Product/Offer

Define your product with value propositions and ideal customer profile.

**Endpoint:** `POST /api/offer/`

**cURL:**
```bash
curl -X POST http://localhost:8000/api/offer/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI Outreach Automation",
    "value_props": [
      "24/7 automated outreach",
      "6x more qualified meetings",
      "Personalized messaging at scale"
    ],
    "ideal_use_cases": [
      "B2B SaaS",
      "Sales teams",
      "Marketing agencies"
    ]
  }'
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "AI Outreach Automation",
  "value_props": [
    "24/7 automated outreach",
    "6x more qualified meetings",
    "Personalized messaging at scale"
  ],
  "ideal_use_cases": [
    "B2B SaaS",
    "Sales teams",
    "Marketing agencies"
  ],
  "created_at": "2025-10-04T10:30:00Z"
}
```

---

### 2. Upload Leads (CSV)

Upload a CSV file containing lead information.

**Endpoint:** `POST /api/leads/upload/`

**CSV Format Requirements:**
```csv
name,role,company,industry,location,linkedin_bio
John Doe,CEO,TechCorp,B2B SaaS,New York,15 years building enterprise SaaS platforms
Jane Smith,Head of Sales,DataFlow,B2B SaaS,San Francisco,Leading sales teams in scaling startups
Mike Wilson,Manager,CloudTech,Healthcare,London,Technology implementation specialist
```

**cURL:**
```bash
curl -X POST http://localhost:8000/api/leads/upload/ \
  -F "file=@leads.csv"
```

**Response (201 Created):**
```json
[
  {
    "id": 1,
    "name": "John Doe",
    "role": "CEO",
    "company": "TechCorp",
    "industry": "B2B SaaS",
    "location": "New York",
    "linkedin_bio": "15 years building enterprise SaaS platforms",
    "intent": null,
    "score": null,
    "reasoning": null,
    "created_at": "2025-10-04T10:35:00Z"
  }
]
```

---

### 3. Score Leads (Hybrid Pipeline)

Run the hybrid scoring pipeline on all unscored leads.

**Endpoint:** `POST /api/leads/score/`

**cURL:**
```bash
curl -X POST http://localhost:8000/api/leads/score/
```

**Response (200 OK):**
```json
{
  "results": [
    {
      "name": "John Doe",
      "role": "CEO",
      "company": "TechCorp",
      "intent": "High",
      "score": 90,
      "reasoning": "[Rule: Decision maker role (+20), Exact ICP match (+20), Complete profile (+10)] [AI: CEO in B2B SaaS with 15 years enterprise experience. Perfect ICP match with clear decision authority.]",
      "score_breakdown": {
        "rule_score": 50,
        "ai_score": 50
      }
    },
    {
      "name": "Jane Smith",
      "role": "Head of Sales",
      "company": "DataFlow",
      "intent": "High",
      "score": 80,
      "reasoning": "[Rule: Decision maker role (+20), Exact ICP match (+20), Complete profile (+10)] [AI: Head of Sales in scaling startup shows buying authority and relevant pain points.]",
      "score_breakdown": {
        "rule_score": 50,
        "ai_score": 30
      }
    }
  ],
  "total_scored": 2,
  "scoring_method": "hybrid (rule + AI)"
}
```

---

### 4. Get Scored Results (Paginated)

Retrieve all scored leads with pagination.

**Endpoint:** `GET /api/leads/results/`

**cURL:**
```bash
# Get first page
curl -X GET http://localhost:8000/api/leads/results/

# Get specific page
curl -X GET "http://localhost:8000/api/leads/results/?page=2"
```

**Response (200 OK):**
```json
{
  "count": 3,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "John Doe",
      "role": "CEO",
      "company": "TechCorp",
      "industry": "B2B SaaS",
      "location": "New York",
      "linkedin_bio": "15 years building enterprise SaaS platforms",
      "intent": "High",
      "score": 90,
      "reasoning": "[Rule: Decision maker role (+20), Exact ICP match (+20), Complete profile (+10)] [AI: CEO in B2B SaaS with extensive experience.]",
      "created_at": "2025-10-04T10:35:00Z"
    }
  ]
}
```

---

### 5. Export Results as CSV (Bonus Feature)

Download all scored leads as a CSV file.

**Endpoint:** `GET /api/leads/export_csv/`

**cURL:**
```bash
curl -X GET http://localhost:8000/api/leads/export_csv/ \
  --output leads_export.csv
```

**Browser:**
Simply visit: `http://localhost:8000/api/leads/export_csv/`

**Downloaded CSV:**
```csv
Name,Role,Company,Industry,Location,Intent,Score,Reasoning
John Doe,CEO,TechCorp,B2B SaaS,New York,High,90,[Rule: Decision maker role (+20)...] [AI: CEO in B2B SaaS...]
Jane Smith,Head of Sales,DataFlow,B2B SaaS,San Francisco,High,80,[Rule: Decision maker role (+20)...] [AI: Head of Sales...]
```

---

## Testing

### Run Unit Tests
```bash
python manage.py test
```

**Expected Output:**
```
Creating test database...
...
----------------------------------------------------------------------
Ran 5 tests in 0.234s

OK
```

### Run with Coverage
```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

### Run API Integration Tests
```bash
# Make sure server is running first
python manage.py runserver

# In another terminal:
python test_api.py
```

**What it tests:**
- Offer creation
- CSV lead upload
- Hybrid scoring pipeline
- Results retrieval

---

## Docker Deployment

### Build and Run with Docker Compose
```bash
docker-compose up --build
```

API available at: `http://localhost:8000`

### Run in Background
```bash
docker-compose up -d
```

### View Logs
```bash
docker-compose logs -f
```

### Stop Containers
```bash
docker-compose down
```

### Rebuild from Scratch
```bash
docker-compose down -v
docker-compose up --build
```

---

## Production Deployment (Render)

This API is deployed on Render with automatic deployments from the main branch.

### Deployment Configuration

**Build Command:** `./build.sh`
```bash
#!/usr/bin/env bash
pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

**Start Command:** `gunicorn main.wsgi:application`

### Required Environment Variables on Render:

| Variable | Value | Description |
|----------|-------|-------------|
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API key |
| `SECRET_KEY` | `random-string` | Django secret key (generate new) |
| `DEBUG` | `False` | Disable debug in production |
| `ALLOWED_HOSTS` | `.onrender.com` | Render domains |

### Generate Secret Key:
```python
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Deployment Steps:

1. Push code to GitHub
2. Connect repository to Render
3. Set environment variables
4. Deploy automatically triggers

**Live URL:** https://buying-intent.onrender.com

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| **Offer Management** |||
| POST | `/api/offer/` | Create new product/offer |
| GET | `/api/offer/` | List all offers |
| GET | `/api/offer/{id}/` | Get specific offer |
| PUT | `/api/offer/{id}/` | Update offer |
| DELETE | `/api/offer/{id}/` | Delete offer |
| **Lead Management** |||
| POST | `/api/leads/upload/` | Upload CSV of leads |
| POST | `/api/leads/score/` | Run hybrid scoring pipeline |
| GET | `/api/leads/results/` | Get scored leads (paginated) |
| GET | `/api/leads/export_csv/` | Export results as CSV |
| GET | `/api/leads/` | List all leads |
| GET | `/api/leads/{id}/` | Get specific lead |
| PUT | `/api/leads/{id}/` | Update specific lead |
| DELETE | `/api/leads/{id}/` | Delete specific lead |
| **Documentation** |||
| GET | `/swagger/` | Swagger UI (interactive docs) |
| GET | `/redoc/` | ReDoc (alternative docs) |
| GET | `/admin/` | Django admin panel |

---

## Project Structure

```
lead-scoring-backend/
├── leads/                      # Main Django app
│   ├── migrations/            # Database migrations
│   ├── __init__.py
│   ├── admin.py               # Admin panel config
│   ├── apps.py                # App configuration
│   ├── models.py              # Lead & Offer models
│   ├── serializers.py         # DRF serializers
│   ├── views.py               # API endpoints (UPDATED)
│   ├── utils.py               # Rule scoring logic (UPDATED)
│   ├── tests.py               # Unit tests
│   └── urls.py                # API routing
├── main/                       # Django project settings
│   ├── __init__.py
│   ├── settings.py            # Project configuration
│   ├── urls.py                # Root URL config + Swagger
│   ├── wsgi.py                # WSGI application
│   └── asgi.py                # ASGI application
├── logs/                       # Application logs
├── staticfiles/               # Collected static files (production)
├── .env                       # Environment variables (not committed)
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
├── build.sh                   # Render deployment script
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── test_api.py                # API integration tests
└── README.md                  # This file (UPDATED)
```

---

## Troubleshooting

### Error: "No offer found" when scoring

**Cause:** No offer created before running scoring pipeline.

**Solution:**
```bash
# Create an offer first
curl -X POST http://localhost:8000/api/offer/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Your Product",
    "value_props": ["Prop 1", "Prop 2"],
    "ideal_use_cases": ["B2B SaaS"]
  }'

# Then run scoring
curl -X POST http://localhost:8000/api/leads/score/
```

---

### Error: "No unscored leads found"

**Cause:** All leads already scored or no leads uploaded.

**Solution:**
```bash
# Upload leads first
curl -X POST http://localhost:8000/api/leads/upload/ \
  -F "file=@leads.csv"

# Then run scoring
curl -X POST http://localhost:8000/api/leads/score/
```

---

### AI scoring returns all Low scores

**Cause:** `OPENAI_API_KEY` not configured or invalid.

**Solution:**
1. Check `.env` file has correct API key:
   ```env
   OPENAI_API_KEY=sk-proj-...
   ```
2. Verify API key at: https://platform.openai.com/api-keys
3. Ensure you have API credits available
4. Restart server after updating `.env`

---

### CSV upload fails

**Cause:** CSV missing required columns or wrong format.

**Solution:**
Ensure CSV has **exact columns** (case-sensitive):
```csv
name,role,company,industry,location,linkedin_bio
```

**Correct:**
```csv
name,role,company,industry,location,linkedin_bio
John Doe,CEO,TechCorp,B2B SaaS,NYC,Bio here
```

**Incorrect:**
```csv
Name,Role,Company,Industry,Location,Bio  (wrong headers)
```

---

### Port 8000 already in use

**Solution:**
```bash
# Use different port
python manage.py runserver 8001

# Or find and kill process using port 8000
# On macOS/Linux:
lsof -ti:8000 | xargs kill -9

# On Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

### OpenAI rate limit errors

**Cause:** API quota exceeded or rate limiting.

**Solution:**
- System automatically falls back to rule-based scoring
- Upgrade OpenAI plan for higher limits
- Wait a few minutes and retry
- Check usage: https://platform.openai.com/usage

---

### Database locked error

**Cause:** Multiple processes accessing SQLite simultaneously.

**Solution:**
```bash
# Stop all running servers
pkill -f runserver

# Delete database and recreate
rm db.sqlite3
python manage.py migrate
```

For production, use PostgreSQL instead of SQLite.

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes* | None | OpenAI API key for AI scoring |
| `SECRET_KEY` | Yes | Auto-generated | Django secret key (keep secret!) |
| `DEBUG` | No | `True` | Enable debug mode (set `False` in prod) |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated allowed hosts |

*Note: AI scoring requires `OPENAI_API_KEY`. System falls back to rule-based scoring only if key is missing.

---

## Assignment Requirements Checklist

### Input APIs
- [x] POST /api/offer/ - Accept product/offer JSON
- [x] POST /api/leads/upload/ - Accept CSV with required columns

### Scoring Pipeline
- [x] Rule Layer (max 50 points)
  - [x] Role relevance: decision maker (+20), influencer (+10)
  - [x] Industry match: exact ICP (+20), adjacent (+10)
  - [x] Data completeness: all fields (+10)
- [x] AI Layer (max 50 points)
  - [x] Send prospect + offer to AI
  - [x] Intent classification: High/Medium/Low
  - [x] Mapping: High=50, Medium=30, Low=10
- [x] Final Score = rule_score + ai_score

### Output APIs
- [x] POST /api/leads/score/ - Run scoring pipeline
- [x] GET /api/leads/results/ - Return JSON with intent & reasoning
- [x] GET /api/leads/export_csv/ - Export as CSV (bonus)

### Submission Requirements
- [x] GitHub repository with proper commit history
- [x] Inline comments & documentation
- [x] README.md with:
  - [x] Setup steps
  - [x] API usage examples (cURL)
  - [x] Explanation of rule logic & prompts
- [x] Deployed backend with live URL
- [x] Unit tests for rule layer (bonus)
- [x] Dockerized service (bonus)

---

## Performance and Scalability

### Current Limits
- **Database:** SQLite (suitable for less than 10K leads)
- **Pagination:** 10 results per page
- **AI Rate Limit:** 60 requests/minute (OpenAI tier dependent)

### Scaling Recommendations

For production scale:

1. **Database:** Switch to PostgreSQL
   ```python
   # settings.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.getenv('DB_NAME'),
           'USER': os.getenv('DB_USER'),
           'PASSWORD': os.getenv('DB_PASSWORD'),
           'HOST': os.getenv('DB_HOST'),
           'PORT': '5432',
       }
   }
   ```

2. **Background Jobs:** Use Celery for async scoring
3. **Caching:** Add Redis for API response caching
4. **Load Balancing:** Deploy multiple instances behind load balancer

---

## Security Best Practices

### Implemented:
- CORS protection
- CSRF protection
- XSS filtering
- Environment variable secrets
- Secure cookies (production)

### Recommendations:
- Add authentication (JWT tokens)
- Rate limiting per IP
- Input validation and sanitization
- HTTPS only (enforced on Render)

---

## Contributing

1. Fork the repository
2. Create a feature branch
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. Make your changes with proper commits
   ```bash
   git commit -m "Add: hybrid scoring implementation"
   ```
4. Push to your branch
   ```bash
   git push origin feature/amazing-feature
   ```
5. Open a Pull Request

---

## License

This project is created for educational/hiring assessment purposes.

---

## Contact and Support

- **Live API:** https://buying-intent.onrender.com
- **API Docs:** https://buying-intent.onrender.com/swagger/
- **Issues:** Open a GitHub issue for bugs or questions

---

## Acknowledgments

- OpenAI GPT-3.5-Turbo for AI-powered intent classification
- Django and Django REST Framework for robust backend architecture
- Render for seamless cloud deployment
- drf-yasg for automatic API documentation

---

Built for B2B lead qualification