# PROCUREX

## Automated Public Procurement Anomaly Detection & Investigation Platform

PROCUREX is a working procurement auditing prototype that analyzes tenders, bids, vendors, contracts and related procurement activity to surface unusual patterns that may warrant human investigation. It combines rule-based and statistical signals with Isolation Forest anomaly detection and relationship analysis to produce explainable investigation priorities.

## Live Prototype

`https://case-hunt-1.preview.emergentagent.com/login`

## Core Features

- Procurement intelligence dashboard
- Investigation case queue
- Explainable anomaly signals
- Repeated-winner analysis
- Price deviation analysis
- Bid clustering analysis
- Low-competition detection
- Bid-rotation pattern detection
- Vendor concentration analysis
- Vendor relationship analysis
- Investigation priority scoring
- CSV data upload
- Case notes and status management
- Procurement comparison
- Investigation reporting

## Architecture

```text
Procurement Data
      |
      v
Validation & Normalization
      |
      v
Feature Engineering
      |
      +----------------------+----------------------+
      |                      |                      |
      v                      v                      v
Statistical Signals     ML Detection       Relationship Analysis
      |                (Isolation Forest)          |
      +----------------------+----------------------+
                             |
                             v
                  Investigation Priority
                             |
                             v
                     Human Investigator
```

## Project Structure

```text
PROCUREX/
|-- frontend/       React + TypeScript application
|-- backend/        FastAPI API and detection engine
|-- data/           Synthetic procurement dataset
|-- README.md       Documentation
|-- START_BACKEND.bat
|-- START_FRONTEND.bat
`-- PROJECT_STRUCTURE.txt
```

## Run Locally

### Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend runs on `http://localhost:8000`.

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

Windows users can also use `START_BACKEND.bat` and `START_FRONTEND.bat`.

## Demo Dataset

The included synthetic dataset contains procurement records and seeded demonstration scenarios covering repeated winners, price anomalies, low competition, bid clustering, bid rotation, vendor relationships, and potential procurement splitting.

All data is synthetic and intended for prototype and demonstration purposes only.

## Responsible Use

PROCUREX is an investigation decision-support system. An anomaly or investigation-priority score does not establish fraud, corruption, collusion, or wrongdoing. The platform is designed to direct authorized investigators toward procurement activity that may deserve further review.

## Technology

- React
- TypeScript
- Tailwind-compatible frontend structure
- Python
- FastAPI
- Pandas
- NumPy
- Scikit-learn
- NetworkX
