"""Local job application tracker — runs on your PC, data stays on disk."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "applications.db"

STATUSES = (
    "Wishlist",
    "Applied",
    "Screening",
    "Interview",
    "Offer",
    "Rejected",
    "Withdrawn",
)

app = Flask(__name__)
app.secret_key = "local-job-tracker-dev-key"


def get_db() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                location TEXT DEFAULT '',
                url TEXT DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Applied',
                applied_on TEXT NOT NULL,
                salary TEXT DEFAULT '',
                follow_up_on TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


@app.context_processor
def inject_globals():
    return {"statuses": STATUSES, "today": date.today().isoformat()}


@app.route("/")
def index():
    status_filter = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()

    sql = "SELECT * FROM applications WHERE 1=1"
    params: list[str] = []

    if status_filter and status_filter in STATUSES:
        sql += " AND status = ?"
        params.append(status_filter)
    if q:
        sql += " AND (company LIKE ? OR role LIKE ? OR location LIKE ? OR notes LIKE ?)"
        like = f"%{q}%"
        params.extend([like, like, like, like])

    sql += """
        ORDER BY
            CASE status
                WHEN 'Interview' THEN 0
                WHEN 'Screening' THEN 1
                WHEN 'Offer' THEN 2
                WHEN 'Applied' THEN 3
                WHEN 'Wishlist' THEN 4
                WHEN 'Withdrawn' THEN 5
                WHEN 'Rejected' THEN 6
                ELSE 7
            END,
            COALESCE(NULLIF(follow_up_on, ''), '9999-12-31'),
            applied_on DESC,
            id DESC
    """

    with get_db() as conn:
        apps = conn.execute(sql, params).fetchall()
        counts = {
            row["status"]: row["c"]
            for row in conn.execute(
                "SELECT status, COUNT(*) AS c FROM applications GROUP BY status"
            )
        }
        total = sum(counts.values())

    return render_template(
        "index.html",
        applications=apps,
        counts=counts,
        total=total,
        status_filter=status_filter,
        q=q,
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        company = request.form.get("company", "").strip()
        role = request.form.get("role", "").strip()
        if not company or not role:
            flash("Company and role are required.", "error")
            return render_template("form.html", app_row=request.form, mode="add")

        status = request.form.get("status", "Applied")
        if status not in STATUSES:
            status = "Applied"

        now = datetime.now().isoformat(timespec="seconds")
        applied_on = request.form.get("applied_on", "").strip() or date.today().isoformat()

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO applications (
                    company, role, location, url, status, applied_on,
                    salary, follow_up_on, notes, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company,
                    role,
                    request.form.get("location", "").strip(),
                    request.form.get("url", "").strip(),
                    status,
                    applied_on,
                    request.form.get("salary", "").strip(),
                    request.form.get("follow_up_on", "").strip(),
                    request.form.get("notes", "").strip(),
                    now,
                    now,
                ),
            )
        flash(f"Saved {company} — {role}.", "ok")
        return redirect(url_for("index"))

    return render_template(
        "form.html",
        app_row={
            "status": "Applied",
            "applied_on": date.today().isoformat(),
        },
        mode="add",
    )


@app.route("/edit/<int:app_id>", methods=["GET", "POST"])
def edit(app_id: int):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (app_id,)
        ).fetchone()

    if row is None:
        flash("Application not found.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        company = request.form.get("company", "").strip()
        role = request.form.get("role", "").strip()
        if not company or not role:
            flash("Company and role are required.", "error")
            return render_template("form.html", app_row=request.form, mode="edit", app_id=app_id)

        status = request.form.get("status", "Applied")
        if status not in STATUSES:
            status = "Applied"

        now = datetime.now().isoformat(timespec="seconds")
        applied_on = request.form.get("applied_on", "").strip() or date.today().isoformat()

        with get_db() as conn:
            conn.execute(
                """
                UPDATE applications SET
                    company = ?, role = ?, location = ?, url = ?, status = ?,
                    applied_on = ?, salary = ?, follow_up_on = ?, notes = ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    company,
                    role,
                    request.form.get("location", "").strip(),
                    request.form.get("url", "").strip(),
                    status,
                    applied_on,
                    request.form.get("salary", "").strip(),
                    request.form.get("follow_up_on", "").strip(),
                    request.form.get("notes", "").strip(),
                    now,
                    app_id,
                ),
            )
        flash(f"Updated {company} — {role}.", "ok")
        return redirect(url_for("index"))

    return render_template("form.html", app_row=row, mode="edit", app_id=app_id)


@app.route("/status/<int:app_id>", methods=["POST"])
def update_status(app_id: int):
    status = request.form.get("status", "")
    if status not in STATUSES:
        flash("Invalid status.", "error")
        return redirect(url_for("index"))

    now = datetime.now().isoformat(timespec="seconds")
    with get_db() as conn:
        conn.execute(
            "UPDATE applications SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, app_id),
        )
    flash(f"Status set to {status}.", "ok")
    return redirect(request.referrer or url_for("index"))


@app.route("/delete/<int:app_id>", methods=["POST"])
def delete(app_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    flash("Deleted.", "ok")
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    print("Job tracker running at http://127.0.0.1:5050")
    print("Data file:", DB_PATH)
    app.run(host="127.0.0.1", port=5050, debug=False)
