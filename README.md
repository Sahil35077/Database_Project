## Laboratory Sample Tracking System

This is a small educational Laboratory Sample Tracking System built with **Python Flask** and **SQLite**.
It demonstrates core database concepts such as entity relationships, many-to-many joins, aggregate queries,
and referential integrity in the context of a realistic lab workflow.

### Tech stack

- **Backend**: Python 3, Flask
- **Database**: SQLite (`lab_samples.db` in the project root)
- **UI**: HTML templates with Bootstrap 5

### Entities and relationships

The schema models the following entities:

- `researcher`: people responsible for collecting samples and conducting experiments.
- `storage_location`: freezers, cold rooms, incubators, cabinets, etc., where samples are stored.
- `sample`: physical samples (soil, water, biological) with metadata and storage info.
- `experiment`: lab experiments that use samples and generate results.
- `experiment_sample`: associative table implementing the many-to-many relationship between experiments and samples.
- `result`: measurement records (e.g., pH, nitrate, OD600, microcystin).

Key relationships:

- One researcher → many samples and many experiments.
- Many-to-many between experiment and sample via `experiment_sample`.
- One experiment → many results; one sample → many results.
- One storage location → many samples.

### Features implemented

- **Insert records**
  - Add researchers, storage locations, samples, experiments (with associated samples), and results.
- **Search and listing**
  - Search samples by type, collection date range, and storage location.
  - List experiments by responsible researcher.
  - List results for a specific experiment.
  - List samples stored in a specific location.
- **Interesting queries**
  - **Sample traceability**: join `sample`, `result`, `experiment`, and `researcher` to show who ran which experiment and what measurements were obtained for a given sample.
  - **Storage summary**: aggregate query (COUNT + GROUP BY) to show how many samples are stored in each storage location.
- **Update**
  - Edit researchers, storage locations, samples (including storage location), experiments (including sample set and status), and results.
- **Delete with integrity rules**
  - Delete samples only if they have no associated results.
  - Delete experiments only if they have no associated results.
  - Delete individual results freely.

Foreign keys and `PRAGMA foreign_keys = ON` are used to enforce referential integrity at the database level.

### Generated sample data

The database is automatically seeded with realistic-looking data when first initialized:

- 5 researchers across different roles and departments.
- 6 storage locations (freezers, cold room shelves, incubator, cabinet, field cooler).
- Multiple soil, water, and biological samples collected on different dates and stored in specific locations.
- Experiments such as:
  - River Water Quality Survey
  - Soil Nutrient Profile
  - E. coli Growth Curve
  - Algal Toxin Screening
- Measurement results including pH, nitrate, conductivity, OD600, and microcystin, linked to both experiments and samples.

### How to run the application

1. **Create and activate a virtual environment (if not already active)**:

   ```bash
   cd project/Code
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Initialize the database and start the Flask app**:

   ```bash
   python app.py
   ```

   The first run will create `lab_samples.db`, the tables, and populate them with sample data.

4. **Open the website**:

   Visit `http://127.0.0.1:5000` in your browser.

You can now explore inserts, updates, deletes, and run the interesting join and aggregate queries via the navigation bar.

### Generate additional test data

If you want a larger, richer dataset (more samples, experiments, and results), you can generate extra records on top
of the existing data using:

```bash
cd project/Code
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
python db.py --more
```

This command will:

- Insert additional automatically generated samples using realistic codes (e.g. `S-2025-100`, `W-2025-105`, …).
- Create extra experiments that focus on different sample types.
- Link samples to those experiments and insert multiple new measurement results per sample–experiment pair.

You can run `python db.py --more` multiple times if you need an even larger dataset; codes and links are generated
to avoid collisions with previously inserted records.

