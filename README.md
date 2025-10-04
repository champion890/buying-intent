# Lead Scoring API

## Setup Instructions
## 1. Setup

1. Clone the repository
2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy `.env.example` to `.env`
- Add your OpenAI API key

5. Run migrations:
```bash
python manage.py migrate
```

## API Endpoints

### 1. Create Offer
```bash
curl -X POST http://localhost:8001/api/offer/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AI Outreach Automation",
    "value_props": ["24/7 outreach", "6x more meetings"],
    "ideal_use_cases": ["B2B SaaS mid-market"]
  }'
```

### 2. Upload Leads
```bash
curl -X POST http://localhost:8000/api/leads/upload/ \
  -F "file=@leads.csv"
```

### 3. Score Leads
```bash
curl -X POST http://localhost:8000/api/leads/score/
```

### 4. Get Results
```bash
curl http://localhost:8000/api/leads/results/
```

## Docker Deployment

```bash
docker-compose up --build
```

## Testing

```bash
python manage.py test
```

## Scoring Logic

The final score (0-100) is a combination of a rule-based score and an AI-based score.
**Final Score = Rule Score + AI Score**

### Rule Layer (50 points max):
- **Role relevance (20 points):** Decision makers (e.g., C-level, VP, Head) get +20, while influencers (e.g., Manager, Lead) get +10.
- **Industry match (20 points):** An exact match with the offer's ideal use cases gets +20, while an adjacent match gets +10.
- **Data completeness (10 points):** If all lead fields (name, role, company, industry, location, linkedin_bio) are present, +10 points are awarded.

### AI Layer (50 points max):
The lead's profile and the offer's details are sent to an AI model (GPT-3.5-Turbo) with the following prompt:
> "Classify the lead's buying intent (High/Medium/Low) and provide a 1-2 sentence explanation."

The AI's classification is mapped to points:
- **High** intent = 50 points
- **Medium** intent = 30 points
- **Low** intent = 10 points
