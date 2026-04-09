# Table of Contents

1. [Overview](#overview)
2. [Goals](#goals)
3. [Tech Stack](#tech-stack)
   - [Frontend](#frontend)
   - [Backend](#backend)
   - [Database](#database)
   - [ORM / Database Access](#orm--database-access)
   - [Database Migrations](#database-migrations)
   - [Local Development](#local-development)
   - [Testing](#testing)
   - [Why this stack](#why-this-stack)
4. [System Architecture](#system-architecture)
   - [High-level architecture diagram](#high-level-architecture-diagram)
5. [Request Flow](#request-flow)
   - [Create account](#create-account)
   - [Deposit funds](#deposit-funds)
   - [Issue card](#issue-card)
   - [Process transaction](#process-transaction)
6. [Data Model](#data-model)
   - [hsa_accounts](#1-hsa_accounts)
   - [debit_cards](#2-debit_cards)
   - [deposits](#3-deposits)
   - [transactions](#4-transactions)
   - [Relationship summary](#relationship-summary)
7. [API Design](#api-design)
   - [Accounts](#accounts)
   - [Deposits](#deposits)
   - [Cards](#cards)
   - [Transactions](#transactions)
8. [Qualified Expense Logic](#qualified-expense-logic)
9. [Concurrency Handling](#concurrency-handling)
   - [Problem](#problem)
   - [Solution](#solution)
   - [Deposit handling](#deposit-handling)
   - [Why database locking was chosen](#why-database-locking-was-chosen)
10. [Error Handling](#error-handling)
11. [Project Structure](#project-structure)
12. [Design Tradeoffs](#design-tradeoffs)
13. [Testing Strategy](#testing-strategy)
14. [Local Reviewer Experience](#local-reviewer-experience)

## Overview

This project is a local web application that simulates a Health Savings Account (HSA) platform. It allows a reviewer to create accounts, deposit funds, issue virtual debit cards, and simulate purchases. The system determines whether a transaction is a qualified medical expense and ensures that concurrent transactions cannot incorrectly overdraw the account balance.

The project is designed as a simple full-stack application with a React frontend, a FastAPI backend, and a PostgreSQL database. The main architectural goal is to keep the implementation easy to run locally while still demonstrating clean separation of concerns, durable data persistence, and safe transaction handling.

---

## Goals

The system supports the following required flows:

- Create an HSA account
- Deposit funds into an account
- Issue a virtual debit card
- Process transactions
- Approve only qualified medical expenses
- Prevent negative balances under concurrent transaction load

In addition to the functional requirements, the solution is intended to be easy for a reviewer to run locally and inspect through a simple web UI.

---

## Tech Stack

### Frontend

- React
- Vite
- TypeScript

### Backend

- Python
- FastAPI

### Database

- PostgreSQL

### ORM / Database Access

- SQLAlchemy 2.x

### Database Migrations

- Alembic

### Local Development

- Docker Compose

### Testing

- pytest
- httpx

### Why this stack

This stack was chosen because it balances speed of development with clear architecture. FastAPI and SQLAlchemy provide a clean way to model the domain and expose API endpoints. PostgreSQL provides strong transactional guarantees and row-level locking, which are important for safe concurrent transaction processing. React and Vite make it easy to build a lightweight local UI for reviewers.

---

## System Architecture

The application is organized into three main layers:

1. Frontend client
2. Backend API
3. Database

The frontend provides a local interface for account creation, deposits, card issuance, and transaction simulation. The backend exposes REST endpoints, validates input, applies business rules, and coordinates database operations. The database persists accounts, cards, deposits, and transaction history.

### High-level architecture diagram

```text
┌──────────────────────────────────────────────────────────────┐
│                         React Frontend                       │
│                                                              │
│  - Create Account                                            │
│  - Deposit Funds                                             │
│  - Issue Virtual Card                                        │
│  - Simulate Transactions                                     │
│  - View Account / Card / Transaction History                 │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                │ HTTP / JSON
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                      FastAPI Backend API                     │
│                                                              │
│  Routes / Controllers                                        │
│  - POST /accounts                                            │
│  - GET /accounts                                             │
│  - GET /accounts/{id}                                        │
│  - POST /accounts/{id}/deposits                              │
│  - POST /accounts/{id}/card                                  │
│  - GET /accounts/{id}/card                                   │
│  - POST /transactions                                        │
│  - GET /accounts/{id}/transactions                           │
│                                                              │
│  Service Layer                                               │
│  - Account Service                                           │
│  - Deposit Service                                           │
│  - Card Service                                              │
│  - Transaction Service                                       │
│                                                              │
│  Business Rules                                              │
│  - Qualified expense validation                              │
│  - Balance checks                                            │
│  - Card status validation                                    │
│  - Concurrency-safe transaction processing                   │
└───────────────────────────────┬──────────────────────────────┘
                                │
                                │ SQLAlchemy ORM
                                ▼
┌──────────────────────────────────────────────────────────────┐
│                         PostgreSQL DB                        │
│                                                              │
│  Tables                                                      │
│  - hsa_accounts                                              │
│  - debit_cards                                               │
│  - deposits                                                  │
│  - transactions                                              │
│                                                              │
│  Concurrency Control                                         │
│  - DB transactions                                           │
│  - Row-level locking (SELECT ... FOR UPDATE)                 │
│  - Atomic commit / rollback                                  │
└──────────────────────────────────────────────────────────────┘
```

---

## Request Flow

### Create account

1. The frontend sends a request to create an HSA account.
2. The backend validates the payload.
3. A new `hsa_accounts` record is created with a zero balance.
4. The created account is returned to the frontend.

### Deposit funds

1. The frontend sends a deposit request for an account.
2. The backend validates the amount.
3. A database transaction begins.
4. The account row is locked.
5. The deposit is recorded in the `deposits` table.
6. The account balance is incremented.
7. The transaction commits and the new balance is returned.

### Issue card

1. The frontend sends a request to issue a card for an account.
2. The backend confirms the account exists.
3. A card record is created in `debit_cards`.
4. The new virtual card is returned.

### Process transaction

1. The frontend sends a transaction request containing account, card, merchant, category, and amount.
2. The backend validates the request format.
3. A database transaction begins.
4. The target account row is locked.
5. The backend verifies:
   - the account exists
   - the card exists and is active
   - the merchant category is a qualified medical expense
   - the account balance is sufficient

6. If all checks pass:
   - the transaction is marked approved
   - the balance is reduced

7. If any check fails:
   - the transaction is marked declined
   - the balance is unchanged

8. The transaction result is stored in `transactions`.
9. The database transaction commits.
10. The API returns the approval or decline result.

---

## Data Model

The system uses four main tables.

### 1. `hsa_accounts`

Represents the primary HSA account and stores the current available balance.

Fields:

- `id`
- `account_holder_name`
- `email`
- `balance`
- `created_at`
- `updated_at`

Notes:

- Balance is stored directly on the account for fast lookup.
- Monetary values should use fixed precision types such as `NUMERIC(12, 2)`.

### 2. `debit_cards`

Represents the virtual debit card associated with an HSA account.

Fields:

- `id`
- `account_id`
- `card_token`
- `status`
- `issued_at`

Notes:

- For this assignment, one account can have zero or one active card.
- The system does not need to store real card data because the card is only simulated.

### 3. `deposits`

Represents money added to an HSA account.

Fields:

- `id`
- `account_id`
- `amount`
- `created_at`

Notes:

- Deposits are recorded separately to provide a ledger of incoming funds.

### 4. `transactions`

Represents each purchase attempt, whether approved or declined.

Fields:

- `id`
- `account_id`
- `card_id`
- `merchant_name`
- `merchant_category`
- `amount`
- `status`
- `decline_reason`
- `created_at`

Notes:

- Storing declined transactions is useful for auditing, debugging, and demoing system behavior.
- The simplest way to determine qualification is to rely on `merchant_category`.

### Relationship summary

- One account has many deposits
- One account has many transactions
- One account has zero or one debit card
- One debit card belongs to one account
- One transaction belongs to one account and optionally one card

---

## API Design

The following endpoints are the core API surface for the project.

### Accounts

- `POST /accounts`
  Create a new HSA account

- `GET /accounts`
  List all accounts

- `GET /accounts/{account_id}`
  Get details for a single account

### Deposits

- `POST /accounts/{account_id}/deposits`
  Deposit funds into an account

### Cards

- `POST /accounts/{account_id}/card`
  Issue a virtual card

- `GET /accounts/{account_id}/card`
  Fetch card details for an account

### Transactions

- `POST /transactions`
  Process a purchase transaction

- `GET /accounts/{account_id}/transactions`
  View transaction history for an account

This endpoint set maps directly to the required reviewer flows while keeping the API simple and easy to understand.

---

## Qualified Expense Logic

The system must determine whether a purchase is a qualified medical expense. For the MVP, the backend uses the transaction’s `merchant_category` field to make this decision.

### Example categories

Approved:

- `pharmacy`
- `hospital`
- `clinic`
- `medical`

Declined:

- `restaurant`
- `electronics`
- `entertainment`

---

## Concurrency Handling

Concurrency is one of the most important requirements in this assignment. The system must correctly handle the case where multiple transactions attempt to spend from the same account at the same time.

### Problem

Assume an account has a balance of `$100.00` and two transactions arrive at nearly the same time:

- Transaction A = `$80.00`
- Transaction B = `$50.00`

If both requests read the balance before either updates it, both could incorrectly approve. That would violate the requirement that the balance never becomes negative.

### Solution

The backend processes spending inside a database transaction and locks the account row before reading or updating the balance.

Recommended approach:

1. Start a database transaction
2. Fetch the account row using `SELECT ... FOR UPDATE`
3. Check card validity
4. Check qualified expense status
5. Check available balance
6. Approve or decline the transaction
7. Update balance only if approved
8. Insert the transaction record
9. Commit the database transaction

Because the account row is locked, concurrent transaction attempts against the same account are serialized. Only one request can update the balance at a time.

### Deposit handling

Deposits use the same strategy:

1. Start a database transaction
2. Lock the account row
3. Insert deposit record
4. Increment balance
5. Commit

This ensures deposits and purchases cannot corrupt the balance if they happen concurrently.

### Why database locking was chosen

This project uses PostgreSQL row-level locking because:

- the database is the source of truth
- it works across multiple workers/processes
- it directly prevents stale reads and lost updates
- it is straightforward to explain in the architecture document and demo

An application-only lock was not chosen because it would not be safe across multiple processes or instances.

---

## Error Handling

The API should return clear failure reasons for invalid or declined requests.

Examples:

- account not found
- card not found
- inactive card
- invalid deposit amount
- invalid merchant category
- non-qualified medical expense
- insufficient funds

For transaction declines, the API should still persist a transaction record with:

- `status = declined`
- a `decline_reason`

---

## Project Structure

```text
backend/
  app/
    api/
      routes/
    core/
      config.py
      database.py
    models/
    schemas/
    services/
    main.py
  alembic/
  tests/

frontend/
  src/
    components/
    pages/
    services/
    types/
    App.tsx
    main.tsx

docker-compose.yml
README.md
architecture.md
ai-usage.md
```

This structure separates API routes, business logic, persistence models, and frontend concerns clearly.

---

## Design Tradeoffs

### Why store current balance on the account?

Storing balance directly on the account simplifies reads and UI rendering. It also makes transaction processing straightforward because the current balance is available in one row. The tradeoff is that balance updates must be handled carefully inside a transaction.

### Why keep deposits and transactions as separate tables?

This gives the system a clearer ledger and better auditability. It also makes the demo easier because the reviewer can inspect both incoming funds and spending history separately.

### Why use merchant category instead of a more advanced qualification engine?

This keeps the implementation simple, predictable, and aligned with the assignment examples. A more complex rules engine could be added later if needed.

### Why use a monolithic app instead of splitting services?

This is a local take-home assignment, so a monolith is the clearest and fastest design. It reduces operational complexity while still allowing clean internal separation between frontend, API, and database layers.

### Why use PostgreSQL instead of SQLite?

PostgreSQL provides stronger support for transactional correctness and row-level locking, which is directly relevant to the concurrency requirement. SQLite could work for a simpler demo, but PostgreSQL is a stronger fit for this problem. [Database Systems]

---

## Testing Strategy

The testing strategy focuses on the highest-risk backend behavior.

### Unit / service tests

- qualified expense validation
- insufficient funds handling
- card validation
- deposit validation

### API tests

- create account
- deposit funds
- issue card
- approve valid transaction
- decline invalid category
- decline insufficient funds

### Concurrency test

A strong extra test is to simulate two concurrent transactions against the same account and verify:

- only one succeeds when funds are insufficient for both
- the final balance is never negative

---

## Local Reviewer Experience

The project is intended to run locally with a simple startup flow. The reviewer should be able to:

- start the backend and database
- start the frontend
- create an account
- deposit funds
- issue a card
- simulate both approved and declined transactions
- observe transaction history and balance updates
