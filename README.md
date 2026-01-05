# 🧠 Advanced Quiz App (PyQt5 + PostgreSQL)

<p align="center">
  <img src="assets/readme_logo.png" alt="DevQuiz Logo" height="720" />
</p>

A desktop **Quiz Application** built with **Python + PyQt5** and backed by **PostgreSQL** (Docker).  
It supports authentication, category-based quizzes, attempt history, and an **Admin panel** to manage questions.

---

## ✨ Overview

This project was built to practice and showcase real-world fundamentals:

- Desktop GUI development with **PyQt5**
- Relational persistence with **PostgreSQL**
- Clean modular UI structure (pages/widgets)
- Basic admin CRUD operations
- User-based statistics and recent activity

---

## ✅ Features

### Authentication
- User login (username + password)
- Create account (unique username enforced by DB)

### Quiz Experience
- Category selection
- Configurable question limit
- Quiz flow (progress + submit)
- Results screen

### Dashboard
- Quick actions (Start Quiz, Admin)
- Stats overview:
  - Total Attempts
  - Best Score
  - Last Score
- Recent Activity list (latest attempts)

### Admin Panel
- Create / edit / delete quiz questions
- Questions stored in PostgreSQL and available immediately

---

## 🛠 Tech Stack

- Python
- PyQt5 (GUI)
- PostgreSQL (Docker + init script)
- psycopg2

---

## 📁 Project Structure

```text
README.md
quiz_app/
  assets/
    quiz_app.png
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

- Access the Admin Panel via Manage Questions in the Dashboard.
- You can add/edit/delete questions inside existing categories.
- Changes are persisted in PostgreSQL and reflected in quizzes immediately.

---

## 📌 Roadmap (Next)

- Improve responsive layout (large vs small window behavior)
- Add validation/messages in Admin form
- Randomize questions + shuffle answers
- Add user roles (admin vs regular user)
- Export/import question sets (JSON)

---

## 🤝 Contributing
Pull requests are welcome! For major changes, please open an issue to discuss what you'd like to change.

---

## 📜 License
MIT License — feel free to use this project for learning or production.

---

## 🧑‍💻 Author
Marcos Vinicius Thibes Kemer

