# Bitespeed Identity Reconciliation

## Project Structure
```
bitespeed_identity/
├── app.py          # Flask entry point + /identify route
├── identity.py     # Core reconciliation logic
├── db.py           # MySQL connection helper
├── config.py       # DB credentials (edit this!)
├── schema.sql      # Run once in MySQL to create DB + table
└── requirements.txt
```

## Setup in PyCharm

### Step 1 — MySQL Setup
1. Open **MySQL Workbench** (or any MySQL client)
2. Open `schema.sql` and run it — this creates `bitespeed_db` and the `Contact` table

### Step 2 — PyCharm Project
1. Open PyCharm → **File > Open** → select the `bitespeed_identity` folder
2. PyCharm will detect it as a Python project

### Step 3 — Virtual Environment
In PyCharm terminal (or bottom panel):
```bash
pip install -r requirements.txt
```

### Step 4 — Configure DB credentials
Edit `config.py` and update:
```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "bitespeed_db"
}
```

### Step 5 — Run
```bash
python app.py
```
Server starts at `http://localhost:3000`

---

## API Usage

### POST /identify

**Request:**
```json
{
  "email": "mcfly@hillvalley.edu",
  "phoneNumber": "123456"
}
```

**Response:**
```json
{
  "contact": {
    "primaryContatctId": 1,
    "emails": ["lorraine@hillvalley.edu", "mcfly@hillvalley.edu"],
    "phoneNumbers": ["123456"],
    "secondaryContactIds": [23]
  }
}
```

### Test with curl
```bash
# New customer
curl -X POST http://localhost:3000/identify \
  -H "Content-Type: application/json" \
  -d '{"email": "doc@hillvalley.edu", "phoneNumber": "88888"}'

# Link with existing
curl -X POST http://localhost:3000/identify \
  -H "Content-Type: application/json" \
  -d '{"email": "emmett@hillvalley.edu", "phoneNumber": "88888"}'
```

---

## Logic Summary

| Scenario | Behaviour |
|---|---|
| No existing contact | Creates new primary contact |
| Match found, same info | Returns existing cluster |
| Match found, new info | Creates secondary contact linked to primary |
| Two separate primaries linked | Older one stays primary, newer turns secondary |
