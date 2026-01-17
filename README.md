# RDBMS Invoicing Demo Application

## Overview

This project consists of two closely related parts:

1. **A custom-built Relational Database Management System (RDBMS)** implemented from scratch.
2. **A minimal invoicing web application** used to demonstrate real-world usage of the RDBMS.

The primary goal of the project is to showcase understanding of relational database concepts such as table definitions, primary and unique keys, indexing, CRUD operations, joins, and basic query parsing. The web application is intentionally simple and exists solely to validate that the database works correctly in a practical scenario.

---

## Project Goals

* Design and implement a simple RDBMS
* Support SQL-like commands and an interactive REPL
* Demonstrate relational concepts (one-to-many, joins, aggregation)
* Integrate the database with a real web application
* Show clear engineering judgment and scope control

This project prioritizes **correctness, clarity, and documentation** over UI complexity or feature breadth.

---

## High-Level Architecture

```
+------------------+        +--------------------+
|  Web Application | <----> |  Custom RDBMS      |
|  (HTTP Server)   |        |  (REPL + Engine)   |
+------------------+        +--------------------+
```

* The web app communicates with the RDBMS using its SQL-like interface
* The RDBMS is responsible for data storage, querying, and constraints
* No external database (e.g. PostgreSQL, MySQL) is used

---

## Data Model

The invoicing domain was chosen because it naturally demonstrates relational database design.

### Tables

#### users

Represents system users who log into the application.

```
users(
  id PRIMARY KEY,
  name,
  email UNIQUE
)
```

#### customers

Represents customers managed by a user. Customers do not authenticate.

```
customers(
  id PRIMARY KEY,
  user_id,
  name,
  email
)
```

#### invoices

Represents an invoice issued to a customer.

```
invoices(
  id PRIMARY KEY,
  customer_id,
  date,
  total
)
```

#### invoice_items

Represents line items belonging to an invoice.

```
invoice_items(
  id PRIMARY KEY,
  invoice_id,
  description,
  amount
)
```

#### payments

Represents payments made toward an invoice.

```
payments(
  id PRIMARY KEY,
  invoice_id,
  amount,
  date
)
```

---

## Design Rationale

### Why invoices and invoice_items are separate

Invoices and invoice items form a **one-to-many relationship**. An invoice is a document, while invoice items are the individual lines on that document. Separating them:

* Avoids data duplication
* Preserves normalization
* Allows aggregation (e.g. calculating totals)
* Enables realistic joins

This mirrors real-world billing systems and demonstrates core relational modeling principles.

---

## Supported Database Features

### Table Management

* CREATE TABLE
* DROP TABLE

### Constraints

* Primary keys
* Unique keys
* Foreign key checks

### CRUD Operations

* INSERT
* SELECT
* UPDATE
* DELETE

### Indexing

* Simple indexes on primary and foreign keys

### Joins

* INNER JOIN between related tables

### Aggregation

* SUM for invoice totals

---

## Example Queries

### Create tables

```
CREATE TABLE customers (
  id INT PRIMARY KEY,
  user_id INT,
  name TEXT,
  email TEXT
);
```

### Insert data

```
INSERT INTO customers VALUES (1, 1, 'Acme Ltd', 'info@acme.com');
```

### Join invoices and customers

```
SELECT customers.name, invoices.id, invoices.total
FROM customers
JOIN invoices ON customers.id = invoices.customer_id;
```

### Calculate invoice totals

```
SELECT invoice_id, SUM(amount)
FROM invoice_items
GROUP BY invoice_id;
```

---

## Web Application Scope

### Purpose

The web application exists only to:

* Demonstrate CRUD operations against the custom RDBMS
* Show real-world usage of joins and constraints
* Validate that the database works beyond the REPL

### Pages

The application intentionally contains a small number of pages:

1. Login
2. Dashboard
3. Customers
4. Invoices
5. Invoice Details (items + totals)
6. Payments (optional)

### Authentication

* Only **users** authenticate
* Customers are data entities only
* Session-based authentication is used

### Authorization

* A user may only access customers and invoices they own
* Authorization is enforced at query level using user_id filters

---

## Security Considerations

* Passwords are stored as hashes (no plaintext)
* Sessions are server-side
* Input validation is applied before executing queries
* The security model is intentionally simple to keep focus on database design

---

## Out of Scope

The following features are intentionally excluded:

* Customer-facing portal
* Email delivery
* Payment gateway integration
* Role-based access control
* Advanced SQL features

These features do not contribute to demonstrating core RDBMS concepts and were omitted deliberately.

---

## Limitations

This RDBMS is a learning and demonstration system and does not aim to be production-ready. Known limitations include:

* Limited SQL grammar
* No query optimizer
* No concurrency control
* No persistence beyond basic storage

These trade-offs are documented intentionally.

---

## How to Run

1. Start the RDBMS REPL
2. Create tables using provided SQL commands
3. Start the web application
4. Access the app in the browser
5. Use the UI to perform CRUD operations

---

## Credits & Acknowledgements

This project was built as part of the **Pesapal Junior Developer Challenge '26**.

AI tools were used as development aids for reasoning and documentation. All design decisions, implementation, and final code structure are my own.

---

## Author

**Juma John Paul**

Junior Developer Candidate – Pesapal JDEV26
