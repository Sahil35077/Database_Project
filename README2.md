# README2

## 1. Relational Schema of the Database

The application uses a relational database for tracking researchers, laboratory samples, storage locations, experiments, the many-to-many use of samples in experiments, and measurement results.

### 1.1 Relations

#### `RESEARCHER`

`RESEARCHER(`  
`id PK,`  
`name,`  
`email UNIQUE,`  
`role,`  
`department`  
`)`

- Primary Key: `id`
- Candidate Key: `email`

#### `STORAGE_LOCATION`

`STORAGE_LOCATION(`  
`id PK,`  
`name,`  
`location_type,`  
`room,`  
`freezer,`  
`shelf,`  
`description`  
`)`

- Primary Key: `id`

#### `SAMPLE`

`SAMPLE(`  
`id PK,`  
`sample_code UNIQUE,`  
`sample_type,`  
`description,`  
`collected_date,`  
`volume_ml,`  
`status,`  
`researcher_id FK -> RESEARCHER(id),`  
`storage_location_id FK -> STORAGE_LOCATION(id)`  
`)`

- Primary Key: `id`
- Candidate Key: `sample_code`
- Foreign Keys:
  - `researcher_id` references `RESEARCHER(id)`
  - `storage_location_id` references `STORAGE_LOCATION(id)`

#### `EXPERIMENT`

`EXPERIMENT(`  
`id PK,`  
`title,`  
`description,`  
`start_date,`  
`end_date,`  
`status,`  
`researcher_id FK -> RESEARCHER(id)`  
`)`

- Primary Key: `id`
- Foreign Key:
  - `researcher_id` references `RESEARCHER(id)`

#### `EXPERIMENT_SAMPLE`

`EXPERIMENT_SAMPLE(`  
`experiment_id FK -> EXPERIMENT(id),`  
`sample_id FK -> SAMPLE(id),`  
`PK(experiment_id, sample_id)`  
`)`

- Composite Primary Key: `(experiment_id, sample_id)`
- Foreign Keys:
  - `experiment_id` references `EXPERIMENT(id)`
  - `sample_id` references `SAMPLE(id)`

#### `RESULT`

`RESULT(`  
`id PK,`  
`experiment_id FK -> EXPERIMENT(id),`  
`sample_id FK -> SAMPLE(id),`  
`measurement_type,`  
`value,`  
`unit,`  
`measured_at,`  
`notes`  
`)`

- Primary Key: `id`
- Foreign Keys:
  - `experiment_id` references `EXPERIMENT(id)`
  - `sample_id` references `SAMPLE(id)`

### 1.2 Main Functional Dependencies

The following functional dependencies hold in the schema:

- `RESEARCHER`
  - `id -> name, email, role, department`
  - `email -> id, name, role, department`

- `STORAGE_LOCATION`
  - `id -> name, location_type, room, freezer, shelf, description`

- `SAMPLE`
  - `id -> sample_code, sample_type, description, collected_date, volume_ml, status, researcher_id, storage_location_id`
  - `sample_code -> id, sample_type, description, collected_date, volume_ml, status, researcher_id, storage_location_id`

- `EXPERIMENT`
  - `id -> title, description, start_date, end_date, status, researcher_id`

- `EXPERIMENT_SAMPLE`
  - `(experiment_id, sample_id) ->` no additional non-key attributes

- `RESULT`
  - `id -> experiment_id, sample_id, measurement_type, value, unit, measured_at, notes`

### 1.3 Normalization Notes

The schema is designed to be well-structured and close to Third Normal Form (3NF):

- Repeating groups are avoided.
- Researcher, sample, experiment, result, and storage information are separated into different relations.
- The many-to-many relationship between experiments and samples is resolved using the associative relation `EXPERIMENT_SAMPLE`.
- Foreign keys enforce referential integrity.
- Candidate keys such as `email` and `sample_code` prevent duplicate logical records.

### 1.4 Referential Integrity Rules

- A sample must reference an existing researcher and storage location.
- An experiment must reference an existing researcher.
- A result must reference an existing experiment and sample.
- A sample or experiment with associated results cannot be deleted.
- `PRAGMA foreign_keys = ON` is used in SQLite to enforce foreign key constraints.

---

## 2. Final Choice of Database and Software Platform

### 2.1 Database Management System

The final database system used in this project is **SQLite3**.

### 2.2 Reason for Choosing SQLite3

SQLite3 was selected because:

- it is lightweight and easy to set up,
- it does not require a separate database server,
- it is fully suitable for a small academic project,
- it supports relational schema design, primary keys, foreign keys, joins, and aggregate queries,
- it integrates very easily with Python and Flask.

For this project, SQLite3 is enough because the goal is to demonstrate core relational database concepts rather than enterprise-scale deployment.

### 2.3 Software Platform / Language

The final software platform is:

- **Backend framework:** Flask
- **Programming language:** Python
- **Database library:** `sqlite3` from Python standard library
- **Frontend:** HTML templates with Jinja2 and Bootstrap
- **Styling and interaction:** CSS and small JavaScript enhancements

### 2.4 Why Flask and Python Were Chosen

Flask with Python was chosen because:

- Flask is simple and suitable for database-driven web applications,
- Python is easy to read, write, and maintain,
- Flask works very well with SQLite,
- it allows the project to be developed quickly while still following good application structure.

Thus, the final technical stack is:

- **Database:** SQLite3
- **Application framework:** Flask
- **Language:** Python
- **UI layer:** HTML/CSS/Bootstrap/Jinja2

---

## 3. Data Source and Data Collection Method

The data for this application is **not collected from a real external database or website**. Instead, it is **manually created and programmatically generated** for academic use.

### 3.1 Source of Data

The application uses **simulated but realistic laboratory data**, including:

- researcher names, roles, and departments,
- sample records such as soil, water, and biological samples,
- storage locations such as freezers, shelves, incubators, and cabinets,
- experiments with statuses and responsible researchers,
- result records such as pH, nitrate, conductivity, OD600, organic matter, and similar measurements.

### 3.2 How the Data Is Generated

The project includes:

- initial seed data written directly in the database initialization script,
- additional automatically generated sample, experiment, and result data through a Python data-generation function.

This means the system contains:

- realistic-looking sample IDs,
- realistic measurement types and units,
- plausible timestamps and experiment histories,
- consistent relational links across all tables.

### 3.3 Why This Approach Was Chosen

This approach was chosen because:

- real laboratory datasets are often private or difficult to access,
- the assignment only requires realistic and relationally meaningful data,
- synthetic data makes it easier to test all CRUD operations and analytical queries,
- it ensures that the schema, joins, and aggregates can be demonstrated clearly.

Therefore, the data is **made up**, but carefully designed to resemble actual laboratory workflows.

---

## 4. Labor Division Among Group Members

### If this is an individual project

If the project is submitted individually, the labor division is:

- **Sahil Thapa**
  - designed the application domain and requirements,
  - created the relational schema and entity relationships,
  - implemented the Flask application,
  - implemented CRUD functionality,
  - created and generated the sample data,
  - designed the user interface,
  - tested and documented the project.

### If this is a group project

If the project is completed in a group, the work can be divided as follows:

- **Member 1 - Database Design**
  - design ER model,
  - define tables, keys, and foreign key constraints,
  - normalize the schema,
  - prepare SQL logic and relational queries.

- **Member 2 - Backend Development**
  - implement Flask routes,
  - connect Flask with SQLite3,
  - implement insert, update, delete, and search logic,
  - enforce referential integrity behavior.

- **Member 3 - Data Preparation and Testing**
  - create realistic sample datasets,
  - generate additional synthetic records,
  - test joins, aggregate queries, and CRUD operations,
  - verify consistency and correctness of data.

- **Member 4 - Frontend and Documentation**
  - create templates and page layout,
  - improve styling and usability,
  - prepare README and report documentation,
  - assist with final integration and presentation.

If you are submitting as a group, replace the labels above with the actual names of your teammates.

---

## 5. Project Timeline with Milestones

The following is a reasonable timeline for the project.

### Week 1 - Planning and Analysis

- select application domain,
- analyze requirements,
- identify core entities and relationships,
- define application functionality,
- draft the ER model.

**Milestone 1:** Application topic and ER design completed.

### Week 2 - Relational Schema Design

- convert ER model into relational schema,
- define primary keys, foreign keys, and constraints,
- identify functional dependencies,
- validate schema structure and normalization.

**Milestone 2:** Final schema completed and approved.

### Week 3 - Database and Backend Setup

- set up Flask project structure,
- create SQLite database,
- implement table creation script,
- connect Flask to SQLite,
- build initial routes.

**Milestone 3:** Database initialized and backend connected.

### Week 4 - CRUD Implementation

- implement researcher, sample, storage, experiment, and result insertion,
- implement update functionality,
- implement deletion rules,
- implement listing pages.

**Milestone 4:** Core CRUD operations working.

### Week 5 - Search and Query Features

- implement sample search by type/date/location,
- implement experiments by researcher,
- implement results by experiment,
- implement samples by storage location,
- implement traceability join query,
- implement storage aggregate query.

**Milestone 5:** Required search and analytical queries completed.

### Week 6 - Data Preparation and Testing

- create initial realistic dataset,
- generate additional synthetic data,
- test relationships and referential integrity,
- test all major pages and forms.

**Milestone 6:** Data loaded and system tested.

### Week 7 - UI Improvement and Final Documentation

- improve frontend appearance,
- refine usability,
- write README and project documentation,
- prepare final submission materials.

**Milestone 7:** Final project completed and ready for submission.

---

## Final Summary

This project uses a normalized relational database implemented in **SQLite3**, with a **Flask + Python** web interface. The data is manually created and generated to simulate realistic laboratory operations. The schema supports traceability, search, aggregation, CRUD operations, and referential integrity. The project timeline and labor division can be adapted depending on whether the work is individual or group-based.

