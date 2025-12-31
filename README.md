# 🧠 Advanced Quiz App (PyQt5 + PostgreSQL)

A desktop **Quiz Application** built with **Python + PyQt5** and backed by **PostgreSQL** (Docker).  
It supports authentication, category-based quizzes, attempt history, and an **Admin panel** to manage questions.

---

## ✅ Features

- **Login** (user authentication)
- **Categories** list (load from database)
- **Quiz flow**
  - next/previous navigation
  - progress bar
  - results screen
- **Dashboard**
  - total attempts
  - best score
  - last score
  - recent attempts table
- **Admin — Manage Questions**
  - create / edit / delete questions inside existing categories
- **Question limit**
  - choose how many questions to load before starting a quiz

---

## 🛠 Tech Stack

- Python
- PyQt5 (GUI)
- PostgreSQL (Docker + init script)
- psycopg2

---

## 📁 Project Structure

```text
quiz_app/
  ui/
    admin.py
    categories.py
    dashboard.py
    login.py
    quiz.py
    results.py
  db.py
  config.py
  main.py
  docker-compose.yml
  init.sql
  requirements.txt
  migrations/
```

---

## 🚀 Getting Started

1) Start PostgreSQL (Docker)
```bash
docker compose up -db
```

2) Create venv + install dependencies
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3) Run the app
```bash
python main.py
```

---

## Admin Panel

- Use “Manage Questions” from the dashboard to add more questions to existing categories.
- New questions are saved to PostgreSQL and immediately available in quizzes.

---

## 📌 Roadmap (Next)

- Improve responsive layout (large vs small window behavior)
- Add validation/messages in Admin form
- Randomize questions + shuffle answers
- Add user roles (admin vs regular user)
- Export/import question sets (JSON)

---
