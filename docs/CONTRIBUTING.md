# Contributing to MAMA CHOL VPN

Thank you for your interest in contributing! This guide explains how to get involved.

---

## Table of Contents

- [Fork and Clone](#fork-and-clone)
- [Development Setup](#development-setup)
- [Code Style Guidelines](#code-style-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting Guidelines](#issue-reporting-guidelines)

---

## Fork and Clone

1. **Fork** the repository on GitHub by clicking the "Fork" button.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Mama-Chol.git
   cd Mama-Chol
   ```
3. Add the upstream remote so you can pull in future changes:
   ```bash
   git remote add upstream https://github.com/nusratneela101/Mama-Chol.git
   ```

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for frontend tooling)
- Docker & Docker Compose (for local services)
- PostgreSQL 15 (or use the Docker Compose stack)

### Backend

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy the example environment file and fill in your values
cp .env.example .env

# Start supporting services (DB, Redis)
docker compose -f deployment/docker-compose.yml up -d db redis

# Apply database migrations
cd backend
alembic upgrade head
cd ..

# Run the development server
uvicorn backend.api.main:app --reload --port 8000
```

### Frontend

The frontend is plain HTML/CSS/JS — just open `frontend/index.html` in a browser,
or serve it with any static file server:

```bash
npx serve frontend
```

### Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

---

## Code Style Guidelines

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/). Use `ruff` or `flake8` to lint.
  ```bash
  pip install ruff
  ruff check backend/ tests/
  ```
- **Docstrings**: All public functions and classes must have docstrings.
- **Type hints**: Use Python type hints for all function signatures.
- **JavaScript**: Follow existing style in `frontend/assets/js/`. Use `const`/`let` (no `var`).
- **HTML/CSS**: Maintain the existing dark/purple design system defined in `style.css`.
- **Commit messages**: Use the imperative mood (e.g. "Add payment webhook handler").

---

## Pull Request Process

1. Create a **feature branch** from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Make your changes and commit them with clear messages.
3. Ensure all tests pass:
   ```bash
   pytest tests/ -v
   ```
4. Lint your code:
   ```bash
   ruff check backend/ tests/
   ```
5. Push your branch and open a **Pull Request** against `main`.
6. Fill in the PR template and describe *what* changed and *why*.
7. A project maintainer will review and may request changes.
8. Once approved and CI passes, the PR will be merged.

---

## Issue Reporting Guidelines

When opening an issue, please include:

- **Title**: Short and descriptive (e.g. "bKash payment fails with 500 error").
- **Environment**: OS, Python version, Docker version.
- **Steps to reproduce**: Numbered list of exact steps.
- **Expected behaviour**: What you expected to happen.
- **Actual behaviour**: What actually happened.
- **Logs / screenshots**: Attach relevant logs or screenshots.

For **security vulnerabilities**, please **do not** open a public issue.
Instead, email the maintainer directly so the issue can be addressed before disclosure.

---

## Code of Conduct

All contributors are expected to be respectful and inclusive.
Harassment or discriminatory behaviour of any kind will not be tolerated.
