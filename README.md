# Clinic Booking API

A robust RESTful backend application for clinic appointment scheduling, booking management, and concurrency-safe reservations built with **FastAPI**, **PostgreSQL**, and **SQLAlchemy 2.0**.

This project is developed as part of the **Koya Academy Cohort 4 Clinic Booking API Assessment**.

---

## 1. Architecture Overview

The system strictly follows a layered architecture to ensure separation of concerns, testability, and maintainability:

```
Client → Controller / Router → Service → Repository → Database (PostgreSQL)
```

- **Controllers (`src/controllers/`)**: Handle HTTP requests, parse DTOs, invoke services, and return standard HTTP responses. They contain no database queries or business rules.
- **Services (`src/services/`)**: Implement business logic (slot availability calculation, booking rules, validation, double-booking prevention, cancellation).
- **Repositories (`src/repositories/`)**: Manage database transactions and CRUD operations via SQLAlchemy 2.0.
- **Models (`src/models/`)**: Represent database entities with proper constraints and indexes.
- **DTOs (`src/dtos/`)**: Define Pydantic request and response contracts strictly complying with the API specification.
- **Config (`src/config/`)**: Centralized application settings (`pydantic-settings`) and SQLAlchemy database engine session management.
- **Middleware (`src/middleware/`)**: Authentication (`X-API-Key`) and cross-cutting concerns.
- **Exceptions (`src/exceptions/`)**: Custom application exceptions and uniform HTTP error handlers.

---

## 2. Technology Stack

- **Language:** Python 3.12+
- **Web Framework:** FastAPI
- **ASGI Server:** Uvicorn
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy 2.0 (using psycopg 3)
- **Migrations:** Alembic
- **Data Validation:** Pydantic v2 & Pydantic-Settings
- **Testing:** Pytest & HTTPX
- **Package & Environment Management:** uv

---

## 3. Directory Structure

```text
.
├── src/
│   ├── __init__.py
│   ├── main.py                     # Application entry point
│   ├── config/                     # Settings and database session management
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── settings.py
│   ├── controllers/                # HTTP route controllers
│   ├── services/                   # Business domain logic
│   ├── repositories/               # Database persistence layer
│   ├── models/                     # SQLAlchemy 2.0 database models
│   ├── dtos/                       # Pydantic schemas / DTOs
│   ├── middleware/                 # API Key authentication & middleware
│   └── exceptions/                 # Error handlers and domain exceptions
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Pytest fixtures (HTTPX async client, sync client)
│   ├── test_health.py              # Health check integration tests
│   ├── controllers/                # Controller layer tests
│   ├── services/                   # Service layer tests
│   └── repositories/               # Repository layer tests
├── migrations/                     # Alembic migration scripts
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── diagrams/                       # Architecture diagrams & ERD
├── .env.example                    # Template environment variables
├── .gitignore                      # Git ignore patterns
├── alembic.ini                     # Alembic configuration
├── pyproject.toml                  # Project metadata and dependencies (managed by uv)
├── uv.lock                         # Exact pinned dependency lockfile
├── PROJECT_DOCUMENTATION.md        # Complete assessment specification & project roadmap
└── README.md                       # Setup and usage guide
```

---

## 4. Setup and Installation

### Prerequisites

- [uv](https://docs.astral.sh/uv/) installed:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- PostgreSQL installed and running (or a remote PostgreSQL instance).

### 1. Clone & Enter Project

```bash
cd /path/to/KOYA
```

### 2. Install Dependencies

Install all dependencies (including development dependencies) into the virtual environment using `uv`:

```bash
uv sync
```

### 3. Environment Configuration

Copy the example environment configuration:

```bash
cp .env.example .env
```

Edit `.env` to configure your API key and PostgreSQL database credentials:

```env
APP_NAME="Clinic Booking API"
APP_ENV="development"
DEBUG=true
API_KEY=your_secret_api_key_here
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/clinic_db
```

---

## 5. Running the Application

Start the development server with hot-reload enabled:

```bash
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative Redoc Documentation:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 6. Running Tests

Execute the automated test suite with Pytest and HTTPX:

```bash
uv run pytest -v
```

---

## 7. Database Migrations

Apply database migrations:

```bash
uv run alembic upgrade head
```

Create a new migration after model changes:

```bash
uv run alembic revision --autogenerate -m "describe migration"
```

---

## 8. Milestone Status

- [x] **Milestone 1:** Project foundation, layered directory structure, dependency management with `uv`, configuration with `pydantic-settings`, database connectivity setup with SQLAlchemy 2.0, Alembic configuration, and Pytest/HTTPX test framework.
- [ ] **Milestone 2:** Database design, ERD, SQLAlchemy models, and Alembic migrations.
- [ ] **Milestone 3:** Slot listing and reset functionality (`POST /reset`, `GET /slots`).
- [ ] **Milestone 4:** Booking creation and retrieval (`POST /bookings`, `GET /bookings/{id}`).
- [ ] **Milestone 5:** API key authentication and request validation.
- [ ] **Milestone 6:** Concurrency protection (double-booking prevention) and cancellation (`DELETE /bookings/{id}`).
- [ ] **Milestone 7:** Comprehensive test suite and verification.
- [ ] **Milestone 8:** Frontend interface.
- [ ] **Milestone 9:** Deployment and live verification.
