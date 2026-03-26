import random
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List

DB_PATH = Path(__file__).parent / "lab_samples.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Schema
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS researcher (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            email           TEXT UNIQUE NOT NULL,
            role            TEXT NOT NULL,
            department      TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS storage_location (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            name            TEXT NOT NULL,
            location_type   TEXT NOT NULL,
            room            TEXT,
            freezer         TEXT,
            shelf           TEXT,
            description     TEXT
        );

        CREATE TABLE IF NOT EXISTS sample (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            sample_code         TEXT NOT NULL UNIQUE,
            sample_type         TEXT NOT NULL,
            description         TEXT,
            collected_date      TEXT NOT NULL,
            volume_ml           REAL,
            status              TEXT NOT NULL,
            researcher_id       INTEGER NOT NULL,
            storage_location_id INTEGER NOT NULL,
            FOREIGN KEY (researcher_id) REFERENCES researcher(id) ON DELETE RESTRICT,
            FOREIGN KEY (storage_location_id) REFERENCES storage_location(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS experiment (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            description     TEXT,
            start_date      TEXT NOT NULL,
            end_date        TEXT,
            status          TEXT NOT NULL,
            researcher_id   INTEGER NOT NULL,
            FOREIGN KEY (researcher_id) REFERENCES researcher(id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS experiment_sample (
            experiment_id   INTEGER NOT NULL,
            sample_id       INTEGER NOT NULL,
            PRIMARY KEY (experiment_id, sample_id),
            FOREIGN KEY (experiment_id) REFERENCES experiment(id) ON DELETE CASCADE,
            FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS result (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            experiment_id       INTEGER NOT NULL,
            sample_id           INTEGER NOT NULL,
            measurement_type    TEXT NOT NULL,
            value               REAL NOT NULL,
            unit                TEXT NOT NULL,
            measured_at         TEXT NOT NULL,
            notes               TEXT,
            FOREIGN KEY (experiment_id) REFERENCES experiment(id) ON DELETE RESTRICT,
            FOREIGN KEY (sample_id) REFERENCES sample(id) ON DELETE RESTRICT
        );
        """
    )

    # Seed data only if empty
    cur.execute("SELECT COUNT(*) FROM researcher;")
    if cur.fetchone()[0] == 0:
        seed_data(conn)

    conn.commit()
    conn.close()


def seed_data(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()

    # Researchers
    researchers = [
        ("Dr. Alice Smith", "alice.smith@lab.edu", "Principal Investigator", "Environmental Science"),
        ("Dr. Bob Johnson", "bob.johnson@lab.edu", "Senior Scientist", "Microbiology"),
        ("Dr. Carol Lee", "carol.lee@lab.edu", "Postdoctoral Researcher", "Water Quality"),
        ("Eve Martinez", "eve.martinez@lab.edu", "Lab Technician", "Soil Chemistry"),
        ("Tom Brown", "tom.brown@lab.edu", "Graduate Student", "Ecotoxicology"),
    ]
    cur.executemany(
        "INSERT INTO researcher (name, email, role, department) VALUES (?, ?, ?, ?);",
        researchers,
    )

    # Storage locations
    locations = [
        ("Freezer A - Rack 1", "Freezer", "Room 101", "Freezer A", "Rack 1", "Long-term storage for soil cores."),
        ("Freezer A - Rack 2", "Freezer", "Room 101", "Freezer A", "Rack 2", "Water samples at -20°C."),
        ("Cold Room Shelf 3", "Cold Room", "Room 110", None, "Shelf 3", "Short-term storage of biological extracts."),
        ("Incubator 37C", "Incubator", "Room 115", None, None, "Bacterial culture incubator at 37°C."),
        ("Chemical Cabinet B", "Cabinet", "Room 103", None, "Shelf B", "Standards and chemical reagents."),
        ("Field Cooler", "Cooler", "Field", None, None, "Portable cooler used during field sampling."),
    ]
    cur.executemany(
        """
        INSERT INTO storage_location
        (name, location_type, room, freezer, shelf, description)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        locations,
    )

    # Map researcher and location IDs
    cur.execute("SELECT id, email FROM researcher;")
    researchers_map = {row["email"]: row["id"] for row in cur.fetchall()}
    cur.execute("SELECT id, name FROM storage_location;")
    locations_map = {row["name"]: row["id"] for row in cur.fetchall()}

    # Samples
    samples = [
        ("S-2025-001", "Soil", "Topsoil near river bank", "2025-03-01", 250.0, "Stored",
         researchers_map["eve.martinez@lab.edu"], locations_map["Freezer A - Rack 1"]),
        ("S-2025-002", "Soil", "Subsurface soil 30cm depth", "2025-03-01", 200.0, "Stored",
         researchers_map["eve.martinez@lab.edu"], locations_map["Freezer A - Rack 1"]),
        ("W-2025-010", "Water", "River water upstream of discharge", "2025-03-05", 500.0, "Stored",
         researchers_map["carol.lee@lab.edu"], locations_map["Freezer A - Rack 2"]),
        ("W-2025-011", "Water", "River water downstream of discharge", "2025-03-05", 500.0, "Stored",
         researchers_map["carol.lee@lab.edu"], locations_map["Freezer A - Rack 2"]),
        ("B-2025-021", "Biological", "Algal culture from reservoir", "2025-03-10", 100.0, "In use",
         researchers_map["tom.brown@lab.edu"], locations_map["Cold Room Shelf 3"]),
        ("S-2025-003", "Soil", "Agricultural field surface", "2025-03-12", 300.0, "Stored",
         researchers_map["eve.martinez@lab.edu"], locations_map["Field Cooler"]),
        ("W-2025-012", "Water", "Groundwater from monitoring well", "2025-03-15", 250.0, "Stored",
         researchers_map["carol.lee@lab.edu"], locations_map["Cold Room Shelf 3"]),
        ("B-2025-022", "Biological", "E. coli test culture", "2025-03-16", 50.0, "In use",
         researchers_map["bob.johnson@lab.edu"], locations_map["Incubator 37C"]),
    ]
    cur.executemany(
        """
        INSERT INTO sample
        (sample_code, sample_type, description, collected_date, volume_ml, status,
         researcher_id, storage_location_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        samples,
    )

    # Experiments
    experiments = [
        (
            "River Water Quality Survey",
            "Assess pH, conductivity, and nitrate levels upstream and downstream.",
            "2025-03-06",
            None,
            "Ongoing",
            researchers_map["carol.lee@lab.edu"],
        ),
        (
            "Soil Nutrient Profile",
            "Determine NPK and organic matter in agricultural and riparian soils.",
            "2025-03-02",
            "2025-03-20",
            "Completed",
            researchers_map["alice.smith@lab.edu"],
        ),
        (
            "E. coli Growth Curve",
            "Monitor optical density over time at 37°C.",
            "2025-03-16",
            None,
            "Ongoing",
            researchers_map["bob.johnson@lab.edu"],
        ),
        (
            "Algal Toxin Screening",
            "Screen algal cultures for microcystin concentration.",
            "2025-03-11",
            None,
            "Ongoing",
            researchers_map["tom.brown@lab.edu"],
        ),
    ]
    cur.executemany(
        """
        INSERT INTO experiment
        (title, description, start_date, end_date, status, researcher_id)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        experiments,
    )

    # Map IDs
    cur.execute("SELECT id, sample_code FROM sample;")
    sample_map = {row["sample_code"]: row["id"] for row in cur.fetchall()}
    cur.execute("SELECT id, title FROM experiment;")
    experiment_map = {row["title"]: row["id"] for row in cur.fetchall()}

    # Experiment-Sample links (many-to-many)
    experiment_samples = [
        (experiment_map["Soil Nutrient Profile"], sample_map["S-2025-001"]),
        (experiment_map["Soil Nutrient Profile"], sample_map["S-2025-002"]),
        (experiment_map["Soil Nutrient Profile"], sample_map["S-2025-003"]),
        (experiment_map["River Water Quality Survey"], sample_map["W-2025-010"]),
        (experiment_map["River Water Quality Survey"], sample_map["W-2025-011"]),
        (experiment_map["River Water Quality Survey"], sample_map["W-2025-012"]),
        (experiment_map["E. coli Growth Curve"], sample_map["B-2025-022"]),
        (experiment_map["Algal Toxin Screening"], sample_map["B-2025-021"]),
    ]
    cur.executemany(
        "INSERT INTO experiment_sample (experiment_id, sample_id) VALUES (?, ?);",
        experiment_samples,
    )

    # Results (measurements)
    now = datetime(2025, 3, 21, 10, 0, 0)
    results = [
        # Soil Nutrient Profile results
        (experiment_map["Soil Nutrient Profile"], sample_map["S-2025-001"], "pH", 6.5, "", "2025-03-05 09:00:00",
         "Slightly acidic riverbank soil."),
        (experiment_map["Soil Nutrient Profile"], sample_map["S-2025-001"], "Nitrate", 15.2, "mg/kg",
         "2025-03-05 09:30:00", None),
        (experiment_map["Soil Nutrient Profile"], sample_map["S-2025-002"], "pH", 7.1, "", "2025-03-05 10:00:00",
         "Neutral subsurface soil."),
        (experiment_map["Soil Nutrient Profile"], sample_map["S-2025-003"], "Organic Matter", 3.8, "%",
         "2025-03-06 11:15:00", "High organic content in agricultural field."),
        # River Water Quality Survey results
        (experiment_map["River Water Quality Survey"], sample_map["W-2025-010"], "pH", 7.4, "",
         "2025-03-06 14:00:00", "Upstream sample."),
        (experiment_map["River Water Quality Survey"], sample_map["W-2025-011"], "pH", 7.1, "",
         "2025-03-06 14:20:00", "Downstream of discharge."),
        (experiment_map["River Water Quality Survey"], sample_map["W-2025-010"], "Nitrate", 2.3, "mg/L",
         "2025-03-06 15:00:00", None),
        (experiment_map["River Water Quality Survey"], sample_map["W-2025-011"], "Nitrate", 6.7, "mg/L",
         "2025-03-06 15:20:00", "Elevated nitrate downstream."),
        (experiment_map["River Water Quality Survey"], sample_map["W-2025-012"], "Conductivity", 510, "µS/cm",
         "2025-03-07 10:00:00", "Groundwater sample."),
        # E. coli Growth Curve results
        (experiment_map["E. coli Growth Curve"], sample_map["B-2025-022"], "OD600", 0.2, "",
         "2025-03-16 09:00:00", "Time 0h."),
        (experiment_map["E. coli Growth Curve"], sample_map["B-2025-022"], "OD600", 0.6, "",
         "2025-03-16 11:00:00", "Time 2h."),
        (experiment_map["E. coli Growth Curve"], sample_map["B-2025-022"], "OD600", 1.1, "",
         "2025-03-16 13:00:00", "Time 4h; mid-log phase."),
        # Algal Toxin Screening
        (experiment_map["Algal Toxin Screening"], sample_map["B-2025-021"], "Microcystin", 0.3, "µg/L",
         "2025-03-12 16:00:00", "Below detection threshold for concern."),
    ]
    cur.executemany(
        """
        INSERT INTO result
        (experiment_id, sample_id, measurement_type, value, unit, measured_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        results,
    )

    conn.commit()


def generate_more_data(additional_samples: int = 30, additional_experiments: int = 6) -> None:
    """
    Generate additional realistic-looking samples, experiments, and results.

    This can be called on an already-initialized database to grow the dataset.
    """
    conn = get_connection()
    cur = conn.cursor()

    # Existing IDs
    cur.execute("SELECT id FROM researcher;")
    researcher_ids: List[int] = [row["id"] for row in cur.fetchall()]
    cur.execute("SELECT id FROM storage_location;")
    storage_ids: List[int] = [row["id"] for row in cur.fetchall()]

    if not researcher_ids or not storage_ids:
        raise RuntimeError("Database must be initialized with base data before generating more.")

    # ---- Extra samples ----
    sample_types = ["Soil", "Water", "Biological", "Other"]
    type_prefix = {"Soil": "S", "Water": "W", "Biological": "B", "Other": "O"}
    statuses = ["Stored", "In use", "Consumed"]

    # Use a high numeric range to avoid collisions with initial seed codes
    base_number = 100
    base_date = date(2025, 4, 1)

    new_samples = []
    for i in range(additional_samples):
        sample_type = random.choice(sample_types)
        code = f"{type_prefix[sample_type]}-2025-{base_number + i:03d}"
        collected = base_date + timedelta(days=random.randint(0, 90))
        volume = round(random.uniform(50.0, 600.0), 1)
        status = random.choice(statuses)
        researcher_id = random.choice(researcher_ids)
        storage_id = random.choice(storage_ids)
        description = f"Auto-generated {sample_type.lower()} sample #{i + 1}"

        new_samples.append(
            (
                code,
                sample_type,
                description,
                collected.isoformat(),
                volume,
                status,
                researcher_id,
                storage_id,
            )
        )

    cur.executemany(
        """
        INSERT OR IGNORE INTO sample
        (sample_code, sample_type, description, collected_date, volume_ml, status,
         researcher_id, storage_location_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """,
        new_samples,
    )

    # Reload samples after insertion
    cur.execute("SELECT id, sample_type FROM sample;")
    all_samples = [(row["id"], row["sample_type"]) for row in cur.fetchall()]
    all_sample_ids = [sid for sid, _ in all_samples]

    # ---- Extra experiments ----
    experiment_templates = [
        (
            "Seasonal River Monitoring",
            "Monthly tracking of river chemistry across seasons.",
            "Water",
        ),
        (
            "Agricultural Runoff Impact",
            "Nutrient loading from nearby agricultural fields.",
            "Water",
        ),
        (
            "Soil Carbon Sequestration",
            "Organic carbon content of restored soils.",
            "Soil",
        ),
        (
            "Microbial Community Dynamics",
            "Culture-based monitoring of indicator organisms.",
            "Biological",
        ),
        (
            "Groundwater Quality Baseline",
            "Baseline survey of monitoring wells.",
            "Water",
        ),
        (
            "Field Pilot Ecotoxicology",
            "Toxicity screening of composite field samples.",
            "Biological",
        ),
    ]

    random.shuffle(experiment_templates)
    new_experiments = []
    for idx, (title, description, focus_type) in enumerate(experiment_templates[:additional_experiments]):
        start = base_date + timedelta(days=idx * 7)
        # Some experiments are completed, others ongoing
        if random.random() < 0.6:
            end = start + timedelta(days=random.randint(5, 20))
            status = "Completed"
            end_str = end.isoformat()
        else:
            status = "Ongoing"
            end_str = None

        responsible = random.choice(researcher_ids)
        new_experiments.append(
            (
                f"Auto - {title}",
                description,
                start.isoformat(),
                end_str,
                status,
                responsible,
                focus_type,
            )
        )

    cur.executemany(
        """
        INSERT INTO experiment
        (title, description, start_date, end_date, status, researcher_id)
        VALUES (?, ?, ?, ?, ?, ?);
        """,
        [(t, d, s, e, st, rid) for (t, d, s, e, st, rid, _focus) in new_experiments],
    )

    # Map new experiment IDs with their focus type
    cur.execute("SELECT id, title FROM experiment WHERE title LIKE 'Auto - %';")
    auto_experiments = {row["title"]: row["id"] for row in cur.fetchall()}

    experiment_focus = {
        title: focus for (title, _d, _s, _e, _st, _rid, focus) in new_experiments if title in auto_experiments
    }

    # ---- Link samples to experiments and create results ----
    measurement_menu = {
        "Soil": [("pH", ""), ("Nitrate", "mg/kg"), ("Phosphate", "mg/kg"), ("Organic Matter", "%")],
        "Water": [("pH", ""), ("Nitrate", "mg/L"), ("Conductivity", "µS/cm"), ("Dissolved Oxygen", "mg/L")],
        "Biological": [("OD600", ""), ("CFU", "CFU/mL"), ("Chlorophyll-a", "µg/L")],
        "Other": [("Concentration", "mg/L")],
    }

    new_results = []
    new_links = []
    for title, exp_id in auto_experiments.items():
        focus_type = experiment_focus.get(title)
        # Prefer samples of the focus type, but fall back to any
        candidate_samples = [sid for sid, st in all_samples if st == focus_type] or all_sample_ids
        selected_samples = random.sample(candidate_samples, k=min(5, len(candidate_samples)))

        for sid in selected_samples:
            new_links.append((exp_id, sid))
            # 1–3 measurements per sample in each experiment
            mdefs = measurement_menu.get(focus_type or "Other", measurement_menu["Other"])
            for _ in range(random.randint(1, 3)):
                m_type, unit = random.choice(mdefs)
                # Simple value ranges for realism
                if m_type == "pH":
                    value = round(random.uniform(5.5, 8.5), 2)
                elif m_type == "Nitrate" and unit == "mg/L":
                    value = round(random.uniform(0.1, 12.0), 2)
                elif m_type == "Nitrate" and unit == "mg/kg":
                    value = round(random.uniform(5.0, 40.0), 1)
                elif m_type == "Conductivity":
                    value = round(random.uniform(150, 900), 0)
                elif m_type == "Organic Matter":
                    value = round(random.uniform(1.0, 6.0), 2)
                elif m_type == "Dissolved Oxygen":
                    value = round(random.uniform(4.0, 11.0), 2)
                elif m_type == "OD600":
                    value = round(random.uniform(0.05, 1.5), 3)
                elif m_type == "CFU":
                    value = round(10 ** random.uniform(2, 7), 0)
                elif m_type == "Chlorophyll-a":
                    value = round(random.uniform(0.5, 45.0), 2)
                else:
                    value = round(random.uniform(0.1, 100.0), 2)

                measured = datetime(2025, 5, 1) + timedelta(
                    days=random.randint(0, 60), hours=random.randint(0, 10)
                )
                notes = f"Auto-generated {m_type} measurement."

                new_results.append(
                    (
                        exp_id,
                        sid,
                        m_type,
                        float(value),
                        unit,
                        measured.strftime("%Y-%m-%d %H:%M:%S"),
                        notes,
                    )
                )

    cur.executemany(
        "INSERT OR IGNORE INTO experiment_sample (experiment_id, sample_id) VALUES (?, ?);",
        new_links,
    )
    cur.executemany(
        """
        INSERT INTO result
        (experiment_id, sample_id, measurement_type, value, unit, measured_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """,
        new_results,
    )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--more":
        generate_more_data()
        print("Additional data generated.")
    else:
        init_db()
        print(f"Database initialized at {DB_PATH}")

