from datetime import datetime
from typing import Any, Dict, List

from flask import Flask, redirect, render_template, request, url_for, flash

from db import get_connection, init_db


app = Flask(__name__)
app.secret_key = "dev-secret-key-change-me"

# Initialize the database on startup
init_db()


@app.context_processor
def inject_now() -> Dict[str, Any]:
    return {"now": datetime.now()}


@app.route("/")
def index():
    conn = get_connection()
    cur = conn.cursor()

    # Simple counts for dashboard
    cur.execute("SELECT COUNT(*) AS c FROM researcher;")
    researcher_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM sample;")
    sample_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM experiment;")
    experiment_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) AS c FROM result;")
    result_count = cur.fetchone()["c"]

    # Simple analytics for dashboard visualizations
    cur.execute(
        """
        SELECT sample_type, COUNT(*) AS c
        FROM sample
        GROUP BY sample_type
        ORDER BY sample_type;
        """
    )
    sample_type_stats = cur.fetchall()
    max_sample_type_count = max((row["c"] for row in sample_type_stats), default=0)

    cur.execute(
        """
        SELECT status, COUNT(*) AS c
        FROM experiment
        GROUP BY status
        ORDER BY status;
        """
    )
    experiment_status_stats = cur.fetchall()

    # Recent activity for dashboard timeline
    cur.execute(
        """
        SELECT *
        FROM (
            SELECT
                'result' AS activity_type,
                res.measured_at AS activity_time,
                s.sample_code AS sample_code,
                res.measurement_type AS title,
                (CAST(res.value AS TEXT) || ' ' || res.unit) AS detail,
                e.title AS context_text
            FROM result res
            JOIN sample s ON res.sample_id = s.id
            JOIN experiment e ON res.experiment_id = e.id

            UNION ALL

            SELECT
                'sample' AS activity_type,
                s.created_at AS activity_time,
                s.sample_code AS sample_code,
                'Sample added' AS title,
                s.sample_type AS detail,
                sl.name AS context_text
            FROM sample s
            JOIN storage_location sl ON s.storage_location_id = sl.id
            WHERE s.created_at IS NOT NULL
        )
        ORDER BY activity_time DESC
        LIMIT 6;
        """
    )
    recent_activity = cur.fetchall()

    conn.close()
    return render_template(
        "index.html",
        researcher_count=researcher_count,
        sample_count=sample_count,
        experiment_count=experiment_count,
        result_count=result_count,
        sample_type_stats=sample_type_stats,
        max_sample_type_count=max_sample_type_count,
        experiment_status_stats=experiment_status_stats,
        recent_activity=recent_activity,
    )


# ---------- Researchers ----------


@app.route("/researchers")
def list_researchers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM researcher ORDER BY name;")
    researchers = cur.fetchall()
    conn.close()
    return render_template("researchers/list.html", researchers=researchers)


@app.route("/researchers/new", methods=["GET", "POST"])
def create_researcher():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        role = request.form["role"].strip()
        department = request.form["department"].strip()

        if not (name and email and role and department):
            flash("All fields are required.", "danger")
        else:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO researcher (name, email, role, department)
                    VALUES (?, ?, ?, ?);
                    """,
                    (name, email, role, department),
                )
                conn.commit()
                flash("Researcher created successfully.", "success")
                return redirect(url_for("list_researchers"))
            except Exception as exc:  # pragma: no cover - simple demo
                conn.rollback()
                flash(f"Error creating researcher: {exc}", "danger")
            finally:
                conn.close()

    return render_template("researchers/form.html", researcher=None)


@app.route("/researchers/<int:researcher_id>/edit", methods=["GET", "POST"])
def edit_researcher(researcher_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM researcher WHERE id = ?;", (researcher_id,))
    researcher = cur.fetchone()

    if not researcher:
        conn.close()
        flash("Researcher not found.", "warning")
        return redirect(url_for("list_researchers"))

    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip()
        role = request.form["role"].strip()
        department = request.form["department"].strip()

        if not (name and email and role and department):
            flash("All fields are required.", "danger")
        else:
            try:
                cur.execute(
                    """
                    UPDATE researcher
                    SET name = ?, email = ?, role = ?, department = ?
                    WHERE id = ?;
                    """,
                    (name, email, role, department, researcher_id),
                )
                conn.commit()
                flash("Researcher updated successfully.", "success")
                return redirect(url_for("list_researchers"))
            except Exception as exc:  # pragma: no cover - simple demo
                conn.rollback()
                flash(f"Error updating researcher: {exc}", "danger")
            finally:
                conn.close()

    conn.close()
    return render_template("researchers/form.html", researcher=researcher)


# ---------- Storage Locations ----------


@app.route("/locations")
def list_locations():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT sl.*,
               COUNT(s.id) AS sample_count
        FROM storage_location sl
        LEFT JOIN sample s ON s.storage_location_id = sl.id
        GROUP BY sl.id
        ORDER BY sl.name;
        """
    )
    locations = cur.fetchall()
    conn.close()
    return render_template("locations/list.html", locations=locations)


@app.route("/locations/new", methods=["GET", "POST"])
def create_location():
    if request.method == "POST":
        name = request.form["name"].strip()
        location_type = request.form["location_type"].strip()
        room = request.form.get("room", "").strip() or None
        freezer = request.form.get("freezer", "").strip() or None
        shelf = request.form.get("shelf", "").strip() or None
        description = request.form.get("description", "").strip() or None

        if not (name and location_type):
            flash("Name and location type are required.", "danger")
        else:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO storage_location
                    (name, location_type, room, freezer, shelf, description)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (name, location_type, room, freezer, shelf, description),
                )
                conn.commit()
                flash("Storage location created successfully.", "success")
                return redirect(url_for("list_locations"))
            except Exception as exc:  # pragma: no cover
                conn.rollback()
                flash(f"Error creating storage location: {exc}", "danger")
            finally:
                conn.close()

    return render_template("locations/form.html", location=None)


@app.route("/locations/<int:location_id>/edit", methods=["GET", "POST"])
def edit_location(location_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM storage_location WHERE id = ?;", (location_id,))
    location = cur.fetchone()

    if not location:
        conn.close()
        flash("Storage location not found.", "warning")
        return redirect(url_for("list_locations"))

    if request.method == "POST":
        name = request.form["name"].strip()
        location_type = request.form["location_type"].strip()
        room = request.form.get("room", "").strip() or None
        freezer = request.form.get("freezer", "").strip() or None
        shelf = request.form.get("shelf", "").strip() or None
        description = request.form.get("description", "").strip() or None

        if not (name and location_type):
            flash("Name and location type are required.", "danger")
        else:
            try:
                cur.execute(
                    """
                    UPDATE storage_location
                    SET name = ?, location_type = ?, room = ?, freezer = ?, shelf = ?, description = ?
                    WHERE id = ?;
                    """,
                    (name, location_type, room, freezer, shelf, description, location_id),
                )
                conn.commit()
                flash("Storage location updated successfully.", "success")
                return redirect(url_for("list_locations"))
            except Exception as exc:  # pragma: no cover
                conn.rollback()
                flash(f"Error updating storage location: {exc}", "danger")
            finally:
                conn.close()

    conn.close()
    return render_template("locations/form.html", location=location)


# ---------- Samples ----------


def _load_researchers_and_locations() -> Dict[str, List[Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM researcher ORDER BY name;")
    researchers = cur.fetchall()
    cur.execute("SELECT * FROM storage_location ORDER BY name;")
    locations = cur.fetchall()
    conn.close()
    return {"researchers": researchers, "locations": locations}


@app.route("/samples")
def list_samples():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT s.*, r.name AS researcher_name, sl.name AS location_name
        FROM sample s
        JOIN researcher r ON s.researcher_id = r.id
        JOIN storage_location sl ON s.storage_location_id = sl.id
        ORDER BY s.collected_date DESC, s.sample_code;
        """
    )
    samples = cur.fetchall()
    conn.close()
    return render_template("samples/list.html", samples=samples)


@app.route("/samples/new", methods=["GET", "POST"])
def create_sample():
    context = _load_researchers_and_locations()

    if request.method == "POST":
        sample_code = request.form["sample_code"].strip()
        sample_type = request.form["sample_type"].strip()
        description = request.form.get("description", "").strip() or None
        collected_date = request.form["collected_date"].strip()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        volume_ml = request.form.get("volume_ml", "").strip() or None
        status = request.form["status"].strip()
        researcher_id = request.form.get("researcher_id")
        storage_location_id = request.form.get("storage_location_id")

        if not (sample_code and sample_type and collected_date and status and researcher_id and storage_location_id):
            flash("Please fill in all required fields.", "danger")
        else:
            if volume_ml:
                try:
                    volume_ml = float(volume_ml)
                except ValueError:
                    flash("Volume must be a number.", "danger")
                    return render_template("samples/form.html", sample=None, **context)

            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO sample
                    (sample_code, sample_type, description, collected_date, created_at,
                     volume_ml, status, researcher_id, storage_location_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        sample_code,
                        sample_type,
                        description,
                        collected_date,
                        created_at,
                        volume_ml,
                        status,
                        int(researcher_id),
                        int(storage_location_id),
                    ),
                )
                conn.commit()
                flash("Sample created successfully.", "success")
                return redirect(url_for("list_samples"))
            except Exception as exc:  # pragma: no cover
                conn.rollback()
                flash(f"Error creating sample: {exc}", "danger")
            finally:
                conn.close()

    return render_template("samples/form.html", sample=None, **context)


@app.route("/samples/<int:sample_id>/edit", methods=["GET", "POST"])
def edit_sample(sample_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sample WHERE id = ?;", (sample_id,))
    sample = cur.fetchone()

    if not sample:
        conn.close()
        flash("Sample not found.", "warning")
        return redirect(url_for("list_samples"))

    context = _load_researchers_and_locations()

    if request.method == "POST":
        sample_code = request.form["sample_code"].strip()
        sample_type = request.form["sample_type"].strip()
        description = request.form.get("description", "").strip() or None
        collected_date = request.form["collected_date"].strip()
        volume_ml = request.form.get("volume_ml", "").strip() or None
        status = request.form["status"].strip()
        researcher_id = request.form.get("researcher_id")
        storage_location_id = request.form.get("storage_location_id")

        if not (sample_code and sample_type and collected_date and status and researcher_id and storage_location_id):
            flash("Please fill in all required fields.", "danger")
        else:
            if volume_ml:
                try:
                    volume_ml = float(volume_ml)
                except ValueError:
                    flash("Volume must be a number.", "danger")
                    return render_template("samples/form.html", sample=sample, **context)

            try:
                cur.execute(
                    """
                    UPDATE sample
                    SET sample_code = ?, sample_type = ?, description = ?,
                        collected_date = ?, volume_ml = ?, status = ?,
                        researcher_id = ?, storage_location_id = ?
                    WHERE id = ?;
                    """,
                    (
                        sample_code,
                        sample_type,
                        description,
                        collected_date,
                        volume_ml,
                        status,
                        int(researcher_id),
                        int(storage_location_id),
                        sample_id,
                    ),
                )
                conn.commit()
                flash("Sample updated successfully.", "success")
                return redirect(url_for("list_samples"))
            except Exception as exc:  # pragma: no cover
                conn.rollback()
                flash(f"Error updating sample: {exc}", "danger")
            finally:
                conn.close()

    conn.close()
    return render_template("samples/form.html", sample=sample, **context)


@app.route("/samples/<int:sample_id>/delete", methods=["POST"])
def delete_sample(sample_id: int):
    conn = get_connection()
    cur = conn.cursor()
    # Only allow delete if no results exist for this sample
    cur.execute("SELECT COUNT(*) AS c FROM result WHERE sample_id = ?;", (sample_id,))
    if cur.fetchone()["c"] > 0:
        conn.close()
        flash("Cannot delete sample that has associated results.", "danger")
        return redirect(url_for("list_samples"))

    try:
        cur.execute("DELETE FROM sample WHERE id = ?;", (sample_id,))
        conn.commit()
        flash("Sample deleted.", "success")
    except Exception as exc:  # pragma: no cover
        conn.rollback()
        flash(f"Error deleting sample: {exc}", "danger")
    finally:
        conn.close()

    return redirect(url_for("list_samples"))


# ---------- Experiments ----------


def _load_researchers() -> List[Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM researcher ORDER BY name;")
    researchers = cur.fetchall()
    conn.close()
    return researchers


def _load_samples() -> List[Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM sample ORDER BY sample_code;")
    samples = cur.fetchall()
    conn.close()
    return samples


@app.route("/experiments")
def list_experiments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT e.*, r.name AS researcher_name,
               COUNT(DISTINCT es.sample_id) AS sample_count,
               COUNT(DISTINCT res.id) AS result_count
        FROM experiment e
        JOIN researcher r ON e.researcher_id = r.id
        LEFT JOIN experiment_sample es ON es.experiment_id = e.id
        LEFT JOIN result res ON res.experiment_id = e.id
        GROUP BY e.id
        ORDER BY e.start_date DESC, e.title;
        """
    )
    experiments = cur.fetchall()
    conn.close()
    return render_template("experiments/list.html", experiments=experiments)


@app.route("/experiments/new", methods=["GET", "POST"])
def create_experiment():
    researchers = _load_researchers()
    samples = _load_samples()

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form.get("description", "").strip() or None
        start_date = request.form["start_date"].strip()
        end_date = request.form.get("end_date", "").strip() or None
        status = request.form["status"].strip()
        researcher_id = request.form.get("researcher_id")
        sample_ids = request.form.getlist("sample_ids")

        if not (title and start_date and status and researcher_id):
            flash("Please fill in all required fields.", "danger")
        else:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO experiment
                    (title, description, start_date, end_date, status, researcher_id)
                    VALUES (?, ?, ?, ?, ?, ?);
                    """,
                    (title, description, start_date, end_date, status, int(researcher_id)),
                )
                experiment_id = cur.lastrowid

                for sid in sample_ids:
                    cur.execute(
                        "INSERT INTO experiment_sample (experiment_id, sample_id) VALUES (?, ?);",
                        (experiment_id, int(sid)),
                    )

                conn.commit()
                flash("Experiment created successfully.", "success")
                return redirect(url_for("list_experiments"))
            except Exception as exc:  # pragma: no cover
                conn.rollback()
                flash(f"Error creating experiment: {exc}", "danger")
            finally:
                conn.close()

    return render_template(
        "experiments/form.html",
        experiment=None,
        researchers=researchers,
        samples=samples,
        selected_sample_ids=[],
    )


@app.route("/experiments/<int:experiment_id>/edit", methods=["GET", "POST"])
def edit_experiment(experiment_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM experiment WHERE id = ?;", (experiment_id,))
    experiment = cur.fetchone()

    if not experiment:
        conn.close()
        flash("Experiment not found.", "warning")
        return redirect(url_for("list_experiments"))

    cur.execute("SELECT sample_id FROM experiment_sample WHERE experiment_id = ?;", (experiment_id,))
    selected_sample_ids = [row["sample_id"] for row in cur.fetchall()]
    conn.close()

    researchers = _load_researchers()
    samples = _load_samples()

    if request.method == "POST":
        title = request.form["title"].strip()
        description = request.form.get("description", "").strip() or None
        start_date = request.form["start_date"].strip()
        end_date = request.form.get("end_date", "").strip() or None
        status = request.form["status"].strip()
        researcher_id = request.form.get("researcher_id")
        sample_ids = [int(s) for s in request.form.getlist("sample_ids")]

        if not (title and start_date and status and researcher_id):
            flash("Please fill in all required fields.", "danger")
        else:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    UPDATE experiment
                    SET title = ?, description = ?, start_date = ?, end_date = ?,
                        status = ?, researcher_id = ?
                    WHERE id = ?;
                    """,
                    (title, description, start_date, end_date, status, int(researcher_id), experiment_id),
                )

                # Update sample associations
                cur.execute("DELETE FROM experiment_sample WHERE experiment_id = ?;", (experiment_id,))
                for sid in sample_ids:
                    cur.execute(
                        "INSERT INTO experiment_sample (experiment_id, sample_id) VALUES (?, ?);",
                        (experiment_id, sid),
                    )

                conn.commit()
                flash("Experiment updated successfully.", "success")
                return redirect(url_for("list_experiments"))
            except Exception as exc:  # pragma: no cover
                conn.rollback()
                flash(f"Error updating experiment: {exc}", "danger")
            finally:
                conn.close()

    return render_template(
        "experiments/form.html",
        experiment=experiment,
        researchers=researchers,
        samples=samples,
        selected_sample_ids=selected_sample_ids,
    )


@app.route("/experiments/<int:experiment_id>/delete", methods=["POST"])
def delete_experiment(experiment_id: int):
    conn = get_connection()
    cur = conn.cursor()
    # Only allow delete if no results exist
    cur.execute("SELECT COUNT(*) AS c FROM result WHERE experiment_id = ?;", (experiment_id,))
    if cur.fetchone()["c"] > 0:
        conn.close()
        flash("Cannot delete experiment that has associated results.", "danger")
        return redirect(url_for("list_experiments"))

    try:
        cur.execute("DELETE FROM experiment WHERE id = ?;", (experiment_id,))
        conn.commit()
        flash("Experiment deleted.", "success")
    except Exception as exc:  # pragma: no cover
        conn.rollback()
        flash(f"Error deleting experiment: {exc}", "danger")
    finally:
        conn.close()

    return redirect(url_for("list_experiments"))


# ---------- Results ----------


@app.route("/results")
def list_results():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT res.*, e.title AS experiment_title, s.sample_code
        FROM result res
        JOIN experiment e ON res.experiment_id = e.id
        JOIN sample s ON res.sample_id = s.id
        ORDER BY res.measured_at DESC;
        """
    )
    results = cur.fetchall()
    conn.close()
    return render_template("results/list.html", results=results)


@app.route("/results/new", methods=["GET", "POST"])
def create_result():
    experiments = _load_experiments()
    samples = _load_samples()

    if request.method == "POST":
        experiment_id = request.form.get("experiment_id")
        sample_id = request.form.get("sample_id")
        measurement_type = request.form["measurement_type"].strip()
        value = request.form.get("value", "").strip()
        unit = request.form["unit"].strip()
        measured_at = request.form.get("measured_at", "").strip() or datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        notes = request.form.get("notes", "").strip() or None

        if not (experiment_id and sample_id and measurement_type and value and unit):
            flash("Please fill in all required fields.", "danger")
        else:
            try:
                value_f = float(value)
            except ValueError:
                flash("Value must be numeric.", "danger")
                return render_template(
                    "results/form.html", result=None, experiments=experiments, samples=samples
                )

            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute(
                    """
                    INSERT INTO result
                    (experiment_id, sample_id, measurement_type, value, unit, measured_at, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (int(experiment_id), int(sample_id), measurement_type, value_f, unit, measured_at, notes),
                )
                conn.commit()
                flash("Result created successfully.", "success")
                return redirect(url_for("list_results"))
            except Exception as exc:  # pragma: no cover
                conn.rollback()
                flash(f"Error creating result: {exc}", "danger")
            finally:
                conn.close()

    return render_template("results/form.html", result=None, experiments=experiments, samples=samples)


def _load_experiments() -> List[Any]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM experiment ORDER BY start_date DESC;")
    experiments = cur.fetchall()
    conn.close()
    return experiments


@app.route("/results/<int:result_id>/edit", methods=["GET", "POST"])
def edit_result(result_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM result WHERE id = ?;", (result_id,))
    result = cur.fetchone()

    if not result:
        conn.close()
        flash("Result not found.", "warning")
        return redirect(url_for("list_results"))

    experiments = _load_experiments()
    samples = _load_samples()

    if request.method == "POST":
        measurement_type = request.form["measurement_type"].strip()
        value = request.form.get("value", "").strip()
        unit = request.form["unit"].strip()
        measured_at = request.form.get("measured_at", "").strip() or result["measured_at"]
        notes = request.form.get("notes", "").strip() or None

        if not (measurement_type and value and unit):
            flash("Measurement type, value, and unit are required.", "danger")
        else:
            try:
                value_f = float(value)
            except ValueError:
                flash("Value must be numeric.", "danger")
                return render_template(
                    "results/form.html", result=result, experiments=experiments, samples=samples
                )

            try:
                cur.execute(
                    """
                    UPDATE result
                    SET measurement_type = ?, value = ?, unit = ?, measured_at = ?, notes = ?
                    WHERE id = ?;
                    """,
                    (measurement_type, value_f, unit, measured_at, notes, result_id),
                )
                conn.commit()
                flash("Result updated successfully.", "success")
                return redirect(url_for("list_results"))
            except Exception as exc:  # pragma: no cover
                conn.rollback()
                flash(f"Error updating result: {exc}", "danger")
            finally:
                conn.close()

    conn.close()
    return render_template("results/form.html", result=result, experiments=experiments, samples=samples)


@app.route("/results/<int:result_id>/delete", methods=["POST"])
def delete_result(result_id: int):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM result WHERE id = ?;", (result_id,))
        conn.commit()
        flash("Result deleted.", "success")
    except Exception as exc:  # pragma: no cover
        conn.rollback()
        flash(f"Error deleting result: {exc}", "danger")
    finally:
        conn.close()

    return redirect(url_for("list_results"))


# ---------- Search & Interesting Queries ----------


@app.route("/samples/search", methods=["GET", "POST"])
def search_samples():
    context = _load_researchers_and_locations()
    samples = []
    criteria = {
        "sample_type": "",
        "from_date": "",
        "to_date": "",
        "storage_location_id": "",
    }

    if request.method == "POST":
        criteria["sample_type"] = request.form.get("sample_type", "").strip()
        criteria["from_date"] = request.form.get("from_date", "").strip()
        criteria["to_date"] = request.form.get("to_date", "").strip()
        criteria["storage_location_id"] = request.form.get("storage_location_id", "").strip()

        sql = [
            """
            SELECT s.*, r.name AS researcher_name, sl.name AS location_name
            FROM sample s
            JOIN researcher r ON s.researcher_id = r.id
            JOIN storage_location sl ON s.storage_location_id = sl.id
            WHERE 1=1
            """
        ]
        params: List[Any] = []

        if criteria["sample_type"]:
            sql.append("AND s.sample_type = ?")
            params.append(criteria["sample_type"])
        if criteria["from_date"]:
            sql.append("AND s.collected_date >= ?")
            params.append(criteria["from_date"])
        if criteria["to_date"]:
            sql.append("AND s.collected_date <= ?")
            params.append(criteria["to_date"])
        if criteria["storage_location_id"]:
            sql.append("AND s.storage_location_id = ?")
            params.append(int(criteria["storage_location_id"]))

        sql.append("ORDER BY s.collected_date DESC, s.sample_code;")

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(" ".join(sql), params)
        samples = cur.fetchall()
        conn.close()

    return render_template(
        "samples/search.html", samples=samples, criteria=criteria, **context
    )


@app.route("/experiments/by_researcher", methods=["GET", "POST"])
def experiments_by_researcher():
    researchers = _load_researchers()
    experiments = []
    selected_researcher_id = ""

    if request.method == "POST":
        selected_researcher_id = request.form.get("researcher_id", "").strip()
        if selected_researcher_id:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT e.*, r.name AS researcher_name
                FROM experiment e
                JOIN researcher r ON e.researcher_id = r.id
                WHERE r.id = ?
                ORDER BY e.start_date DESC;
                """,
                (int(selected_researcher_id),),
            )
            experiments = cur.fetchall()
            conn.close()

    return render_template(
        "experiments/by_researcher.html",
        researchers=researchers,
        experiments=experiments,
        selected_researcher_id=selected_researcher_id,
    )


@app.route("/results/by_experiment", methods=["GET", "POST"])
def results_by_experiment():
    experiments = _load_experiments()
    results = []
    selected_experiment_id = ""

    if request.method == "POST":
        selected_experiment_id = request.form.get("experiment_id", "").strip()
        if selected_experiment_id:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT res.*, e.title AS experiment_title, s.sample_code
                FROM result res
                JOIN experiment e ON res.experiment_id = e.id
                JOIN sample s ON res.sample_id = s.id
                WHERE e.id = ?
                ORDER BY res.measured_at DESC;
                """,
                (int(selected_experiment_id),),
            )
            results = cur.fetchall()
            conn.close()

    return render_template(
        "results/by_experiment.html",
        experiments=experiments,
        results=results,
        selected_experiment_id=selected_experiment_id,
    )


@app.route("/samples/by_location", methods=["GET", "POST"])
def samples_by_location():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM storage_location ORDER BY name;")
    locations = cur.fetchall()
    samples = []
    selected_location_id = ""

    if request.method == "POST":
        selected_location_id = request.form.get("storage_location_id", "").strip()
        if selected_location_id:
            cur.execute(
                """
                SELECT s.*, r.name AS researcher_name, sl.name AS location_name
                FROM sample s
                JOIN researcher r ON s.researcher_id = r.id
                JOIN storage_location sl ON s.storage_location_id = sl.id
                WHERE sl.id = ?
                ORDER BY s.collected_date DESC, s.sample_code;
                """,
                (int(selected_location_id),),
            )
            samples = cur.fetchall()

    conn.close()
    return render_template(
        "samples/by_location.html",
        locations=locations,
        samples=samples,
        selected_location_id=selected_location_id,
    )


@app.route("/traceability", methods=["GET", "POST"])
def sample_traceability():
    samples = _load_samples()
    trace_rows = []
    selected_sample_id = ""

    if request.method == "POST":
        selected_sample_id = request.form.get("sample_id", "").strip()
        if selected_sample_id:
            conn = get_connection()
            cur = conn.cursor()
            # Multi-table join: SAMPLE, RESULT, EXPERIMENT, RESEARCHER
            cur.execute(
                """
                SELECT
                    s.sample_code,
                    s.sample_type,
                    e.title AS experiment_title,
                    r.name AS researcher_name,
                    res.measurement_type,
                    res.value,
                    res.unit,
                    res.measured_at,
                    res.notes
                FROM result res
                JOIN experiment e ON res.experiment_id = e.id
                JOIN researcher r ON e.researcher_id = r.id
                JOIN sample s ON res.sample_id = s.id
                WHERE res.sample_id = ?
                ORDER BY res.measured_at;
                """,
                (int(selected_sample_id),),
            )
            trace_rows = cur.fetchall()
            conn.close()

    return render_template(
        "traceability.html",
        samples=samples,
        trace_rows=trace_rows,
        selected_sample_id=selected_sample_id,
    )


@app.route("/storage_summary")
def storage_summary():
    conn = get_connection()
    cur = conn.cursor()
    # Aggregate query: COUNT samples by storage location
    cur.execute(
        """
        SELECT
            sl.id,
            sl.name,
            sl.location_type,
            sl.room,
            COUNT(s.id) AS sample_count
        FROM storage_location sl
        LEFT JOIN sample s ON s.storage_location_id = sl.id
        GROUP BY sl.id
        ORDER BY sample_count DESC, sl.name;
        """
    )
    summary = cur.fetchall()
    conn.close()
    return render_template("storage_summary.html", summary=summary)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)

