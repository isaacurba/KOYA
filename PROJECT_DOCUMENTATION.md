# Clinic Booking API

## 1. Project Overview

The Clinic Booking API is a RESTful backend application that allows patients to view available appointment slots, book appointments, retrieve booking confirmations and cancel existing bookings.

The application will also include a simple web interface that allows patients to interact with the booking system without needing to make API requests manually.

This project is being developed as part of the Koya Academy Cohort 4 AI Automation Developer assessment.

### Main objectives

- Display available clinic appointment slots.
- Allow patients to book available appointment slots.
- Prevent multiple patients from booking the same slot.
- Allow patients to retrieve their booking information.
- Allow patients to cancel existing bookings.
- Protect API endpoints using API key authentication.
- Validate incoming booking information.
- Deploy the application to a publicly accessible HTTPS URL.

---

## 2. Assessment Scope

The assessment contains five implementation levels.

For this project, the initial target is Levels 1–3.

| Level | Requirement | Planned |
|---|---|---|
| Level 1 | List appointment slots | Yes |
| Level 1 | Create a booking | Yes |
| Level 1 | Retrieve a booking by ID | Yes |
| Level 2 | API key authentication | Yes |
| Level 2 | Booking input validation | Yes |
| Level 3 | Prevent double booking, including concurrent requests | Yes |
| Level 3 | Cancel a booking | Yes |
| Level 4 | Idempotency | Future improvement |
| Level 4 | Cursor-based booking pagination | Future improvement |
| Level 5 | Per-email rate limiting | Future improvement |

**Important:** The application must implement every requirement in the selected levels correctly before considering additional levels.

---

## 3. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Primary programming language |
| FastAPI | Backend web framework |
| PostgreSQL | Relational database |
| SQLAlchemy 2.0 | Database ORM |
| Pydantic | Request and response validation |
| Alembic | Database migrations |
| Pytest | Automated testing |
| HTTPX | API integration testing |
| uv | Python project and dependency management |
| HTML, CSS and JavaScript | Simple frontend |

---

## 4. Application Architecture

The backend will follow a layered architecture.

The purpose of this architecture is to separate responsibilities and make the application easier to understand, test, maintain and extend.

### Architecture flow

**Client → Router/Controller → Service → Repository → Database**

#### 4.1 Router / Controller

Responsible for receiving HTTP requests and returning HTTP responses.

Responsibilities:
- Define API endpoints.
- Receive request parameters and request bodies.
- Call the appropriate service methods.
- Return the correct response and HTTP status code.

Controllers should not contain database queries or complicated business logic.

#### 4.2 Service

Responsible for implementing the application's business rules.

Responsibilities:
- Validate business conditions.
- Check whether appointment slots exist.
- Determine whether a slot is available.
- Create bookings.
- Prevent double booking.
- Cancel bookings.

#### 4.3 Repository

Responsible for communicating with the database.

Responsibilities:
- Create records.
- Retrieve records.
- Update records.
- Delete records when required.
- Perform database queries.

#### 4.4 Models

Represent the database entities using SQLAlchemy.

#### 4.5 DTOs / Schemas

Define the structure of incoming requests and outgoing responses using Pydantic.

#### 4.6 Database

PostgreSQL will store appointment slots and patient bookings.

---

## 5. Proposed Project Structure

```text
clinic-booking-api/
│
├── src/
│   ├── main.py
│   │
│   ├── config/
│   │   ├── settings.py
│   │   └── database.py
│   │
│   ├── controllers/
│   │   ├── slot_controller.py
│   │   └── booking_controller.py
│   │
│   ├── services/
│   │   ├── slot_service.py
│   │   └── booking_service.py
│   │
│   ├── repositories/
│   │   ├── slot_repository.py
│   │   └── booking_repository.py
│   │
│   ├── models/
│   │   ├── slot.py
│   │   └── booking.py
│   │
│   ├── dtos/
│   │   ├── slot_dto.py
│   │   └── booking_dto.py
│   │
│   ├── middleware/
│   │   └── api_key_auth.py
│   │
│   └── exceptions/
│       └── handlers.py
│
├── tests/
│   ├── conftest.py
│   ├── test_health.py
│   ├── controllers/
│   ├── services/
│   └── repositories/
│
├── migrations/
├── diagrams/
│
├── .env.example
├── .gitignore
├── alembic.ini
├── pyproject.toml
├── PROJECT_DOCUMENTATION.md
└── README.md
```

The structure may be adjusted where necessary, but each file should have a clear responsibility.

---

## 6. Database Design

The initial database will contain two main entities.

### 6.1 Slot

Represents an appointment slot offered by a clinic provider.

| Field | Type | Description |
|---|---|---|
| id | String | Unique slot identifier |
| provider | String | Name of the healthcare provider |
| start | DateTime | Appointment start time |
| end | DateTime | Appointment end time |

### 6.2 Booking

Represents a patient's appointment booking.

| Field | Type | Description |
|---|---|---|
| id | UUID/String | Unique booking identifier |
| slot_id | String | Reference to the booked slot |
| name | String | Patient's full name |
| email | String | Patient's email address |
| status | String/Enum | confirmed or cancelled |
| created_at | DateTime | Date and time the booking was created |

### 6.3 Relationships

- One appointment slot can have multiple booking records over time.
- Only one booking for a slot can have the `confirmed` status at a time.
- A cancelled booking remains in the database.
- Cancelling a booking makes the appointment slot available again.

**Important database rule:**

Preventing double booking must not depend only on checking availability in Python.

The database must enforce the rule as well, so simultaneous requests cannot create two confirmed bookings for the same slot.

With PostgreSQL, a partial unique index on `slot_id` for records whose status is `confirmed` can enforce this rule.

This also allows a patient to cancel a booking and another patient to book that slot later.

---

## 7. API Specification

All API endpoints return JSON.

Every request must include:

```http
X-API-Key: your-api-key
```

A missing or incorrect API key must return HTTP `401 Unauthorized`.

Every error response must follow this format:

```json
{
  "error": "Meaningful error message"
}
```

### 7.1 Reset Appointment Slots

**Endpoint:** `POST /reset`

**Level:** 1

Purpose:
- Delete existing bookings.
- Replace all existing appointment slots with the slots supplied in the request.

Example request:

```json
{
  "slots": [
    {
      "id": "s1",
      "provider": "Dr Ade",
      "start": "2026-12-10T09:00:00Z",
      "end": "2026-12-10T09:30:00Z"
    }
  ]
}
```

Expected response:

```http
200 OK
```

The reset operation must be handled safely as a database transaction.

### 7.2 List Appointment Slots

**Endpoint:** `GET /slots`

**Level:** 1

Purpose:
- Retrieve all appointment slots.
- Return the earliest appointment first.
- Allow filtering by provider.

Optional query parameter:

```text
provider
```

Example:

```http
GET /slots?provider=Dr%20Ade
```

Expected response:

```json
{
  "slots": [
    {
      "id": "s1",
      "provider": "Dr Ade",
      "start": "2026-12-10T09:00:00Z",
      "end": "2026-12-10T09:30:00Z",
      "available": true
    }
  ]
}
```

The `available` field must indicate whether the slot currently has a confirmed booking.

### 7.3 Create a Booking

**Endpoint:** `POST /bookings`

**Levels:** 1, 2 and 3

Purpose:
- Allow a patient to book an appointment slot.
- Validate the patient's information.
- Check slot availability.
- Prevent duplicate confirmed bookings.

Example request:

```json
{
  "slot_id": "s1",
  "name": "Ada Obi",
  "email": "ada@example.com"
}
```

Expected successful response:

```http
201 Created
```

```json
{
  "id": "booking-123",
  "slot_id": "s1",
  "name": "Ada Obi",
  "email": "ada@example.com",
  "status": "confirmed",
  "created_at": "2026-11-15T13:45:52.522Z"
}
```

#### Business rules

1. `slot_id`, `name` and `email` are required.
2. Name and email must not be empty.
3. Email must be valid.
4. Leading and trailing spaces must be removed from name and email.
5. Email must be stored in lowercase.
6. The requested slot must exist.
7. A slot that has already started cannot be booked.
8. A slot with an existing confirmed booking cannot be booked again.
9. Two simultaneous requests must never successfully book the same slot.

#### Expected error responses

| Status | Meaning |
|---|---|
| 400 | Missing or invalid details |
| 401 | Missing or incorrect API key |
| 404 | Appointment slot does not exist |
| 409 | Appointment slot is already booked |

### 7.4 Retrieve a Booking

**Endpoint:** `GET /bookings/{id}`

**Level:** 1

Purpose:
- Retrieve a booking using its unique identifier.

Example:

```http
GET /bookings/booking-123
```

Expected response:

```json
{
  "id": "booking-123",
  "slot_id": "s1",
  "name": "Ada Obi",
  "email": "ada@example.com",
  "status": "confirmed",
  "created_at": "2026-11-15T13:45:52.522Z"
}
```

If the booking does not exist, return:

```http
404 Not Found
```

### 7.5 Cancel a Booking

**Endpoint:** `DELETE /bookings/{id}`

**Level:** 3

Purpose:
- Cancel an existing booking.
- Change its status to `cancelled`.
- Make the associated appointment slot available again.

Example:

```http
DELETE /bookings/booking-123
```

Expected response:

```http
200 OK
```

The response should contain the cancelled booking with:

```json
{
  "status": "cancelled"
}
```

Expected errors:

| Status | Meaning |
|---|---|
| 401 | Missing or incorrect API key |
| 404 | Booking does not exist |
| 409 | Booking has already been cancelled |

---

## 8. Authentication and Security

API key authentication will be implemented for all assessment endpoints.

The API key will be stored in an environment variable rather than hardcoded into the application.

Example:

```env
API_KEY=your-secret-api-key
DATABASE_URL=postgresql+psycopg://user:password@localhost:5432/clinic_db
```

The `.env` file must never be committed to GitHub.

A `.env.example` file will contain placeholder values.

**Frontend security consideration:**

The real API key must not be embedded in public JavaScript or exposed in browser code.

The frontend should communicate through a server-side proxy or backend-for-frontend layer that keeps the API key on the server.

---

## 9. Double-Booking Prevention

This is one of the most important requirements in Level 3.

A simple availability check is not sufficient.

For example:

1. Patient A requests slot `s1`.
2. Patient B requests slot `s1` at almost the same time.
3. Both requests check availability.
4. Both see that the slot is available.
5. Both attempt to create bookings.

Without database-level protection, both bookings could succeed.

The application must use a database-backed concurrency protection strategy.

The recommended approach is a PostgreSQL transaction combined with a database constraint that prevents more than one confirmed booking for the same slot.

The application should return:

```http
409 Conflict
```

when another request has already successfully booked the slot.

---

## 10. Frontend Requirements

The application must include a simple webpage that allows patients to use the booking system.

The webpage should include:

### Appointment Listing
- Display available appointment slots.
- Show provider name.
- Show appointment date.
- Show appointment start and end times.
- Clearly indicate unavailable slots.

### Booking Form
- Patient name.
- Patient email.
- Appointment selection.
- Book appointment button.

### Booking Confirmation
After a successful booking:
- Display a success message.
- Show the booking ID.
- Show the patient's name and email.
- Show the selected appointment details.

### Error Handling
Display understandable messages when:
- A slot is no longer available.
- The patient's details are invalid.
- The requested appointment cannot be found.
- The API is temporarily unavailable.

The interface should be responsive and easy to use.

---

## 11. Testing Strategy

Testing should be done throughout development, not only at the end.

### Slot Tests
- Retrieve all appointment slots.
- Retrieve slots filtered by provider.
- Verify that slots are returned in ascending start-time order.
- Verify that availability is correctly calculated.

### Booking Tests
- Create a valid booking.
- Reject missing names.
- Reject missing emails.
- Reject invalid email addresses.
- Reject nonexistent slots.
- Reject slots that have already started.
- Trim spaces from names and emails.
- Store email addresses in lowercase.

### Concurrency Tests
- Send multiple booking requests for the same slot.
- Confirm that only one request succeeds.
- Confirm that the remaining requests receive conflict responses.

### Cancellation Tests
- Cancel an existing booking.
- Confirm that the booking status changes to `cancelled`.
- Confirm that the slot becomes available again.
- Reject cancellation of an already cancelled booking.

### Authentication Tests
- Reject requests without an API key.
- Reject requests with an incorrect API key.
- Accept requests with the correct API key.

---

## 12. Deployment Requirements

The application must be deployed and accessible through HTTPS.

The deployment must include:

- A publicly accessible API base URL.
- A configured API key.
- A publicly accessible frontend webpage.
- A persistent PostgreSQL database.
- Environment variables configured on the hosting platform.
- A public GitHub repository or repository access for `quadri40`.

The application must continue running after submission and must not be changed until Koya contacts the developer.

---

## 13. Implementation Milestones

Development will be completed in small, verifiable milestones.

| Milestone | Work |
|---|---|
| 1 | Project setup, dependencies and configuration |
| 2 | Database design, SQLAlchemy models and migrations |
| 3 | Slot listing and reset functionality |
| 4 | Booking creation and booking retrieval |
| 5 | API key authentication and request validation |
| 6 | Concurrency protection and booking cancellation |
| 7 | Automated testing and bug fixes |
| 8 | Frontend implementation |
| 9 | Deployment and final verification |

Each milestone should be reviewed and tested before moving to the next.

Git commits should describe the actual work completed.

---

## 14. Future Improvements

After Levels 1–3 are completed successfully, the following features can be considered:

- Idempotency keys to prevent duplicate bookings caused by retried requests.
- Cursor-based pagination for retrieving a patient's bookings.
- Per-email rate limiting to prevent excessive booking attempts.

These features correspond to Levels 4 and 5 of the assessment and are not part of the initial implementation scope.

---

## 15. Definition of Done

The initial project will be considered complete when:

- [ ] Patients can view appointment slots.
- [ ] Patients can filter slots by provider.
- [ ] Patients can book available slots.
- [ ] Patients can retrieve bookings using their booking IDs.
- [ ] Invalid booking information is rejected.
- [ ] API key authentication works on every required endpoint.
- [ ] Two patients cannot book the same slot simultaneously.
- [ ] Patients can cancel bookings.
- [ ] Cancelled slots become available again.
- [ ] Automated tests pass.
- [ ] The frontend communicates successfully with the backend.
- [ ] The API and webpage are deployed using HTTPS.
- [ ] The application uses persistent database storage.
- [ ] The GitHub repository contains clear setup instructions.

**Final priority:** Correctness, reliability, clean architecture and a working demonstration are more important than implementing every assessment level.