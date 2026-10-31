
from functools import wraps
import os
from dotenv import load_dotenv

from flask import Flask, render_template, request, redirect, url_for, abort
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user,
)
from models import db, Incident, User


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

app = Flask(__name__)

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///incidents.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# --------------------------------------------------
# Database setup and demo accounts
# --------------------------------------------------

with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="Admin")
        admin.set_password("ChangeMe123!")
        db.session.add(admin)

    if not User.query.filter_by(username="reporter").first():
        reporter = User(username="reporter", role="Reporter")
        reporter.set_password("Reporter123!")
        db.session.add(reporter)

    
    if not User.query.filter_by(username="agent").first():
        agent = User(username="agent", role="Agent")
        agent.set_password("Agent123!")
        db.session.add(agent)


    db.session.commit()


# --------------------------------------------------
# Authentication and role helpers
# --------------------------------------------------

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def roles_required(*roles):
    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)

            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator

# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def landing():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    return render_template("home.html")



# Dashboard with live incident statistics
@app.route("/dashboard")
@login_required
def home():
    incidents = Incident.query.order_by(
        Incident.created_at.desc()
    ).all()

    total_incidents = Incident.query.count()
    open_incidents = Incident.query.filter_by(
        status="Open"
    ).count()
    in_progress_incidents = Incident.query.filter_by(
        status="In Progress"
    ).count()
    resolved_incidents = Incident.query.filter_by(
        status="Resolved"
    ).count()
    critical_incidents = Incident.query.filter_by(
        priority="Critical"
    ).count()

    return render_template(
        "index.html",
        incidents=incidents,
        total_incidents=total_incidents,
        open_incidents=open_incidents,
        in_progress_incidents=in_progress_incidents,
        resolved_incidents=resolved_incidents,
        critical_incidents=critical_incidents,
    )



# --------------------------------------------------
# Create incident through website form
# --------------------------------------------------

@app.route("/incidents", methods=["POST"])
@login_required
def create_incident():
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    priority = request.form.get("priority", "Medium")
    assigned_to = request.form.get("assigned_to", "").strip() or None

    if not title or not description:
        return "Title and description are required.", 400

    if priority not in {"Low", "Medium", "High", "Critical"}:
        return "Invalid priority.", 400

    incident = Incident(
        title=title,
        description=description,
        priority=priority,
        assigned_to=assigned_to,
    )

    db.session.add(incident)
    db.session.commit()

    return redirect(url_for("home"))


# --------------------------------------------------
# Update incident through website form
# Only Admins and Agents can update
# --------------------------------------------------

@app.route("/incidents/<int:incident_id>/update", methods=["POST"])
@roles_required("Admin", "Agent")
def update_incident(incident_id):
    incident = db.session.get(Incident, incident_id)

    if incident is None:
        return "Incident not found.", 404

    new_status = request.form.get("status", "")
    assigned_to = request.form.get("assigned_to", "").strip()

    if new_status not in {"Open", "In Progress", "Resolved"}:
        return "Invalid incident status.", 400

    if len(assigned_to) > 100:
        return "Technician name must be 100 characters or fewer.", 400

    incident.status = new_status
    incident.assigned_to = assigned_to or None

    db.session.commit()

    return redirect(url_for("home"))


# --------------------------------------------------
# REST API: GET all incidents
# --------------------------------------------------

@app.route("/api/incidents", methods=["GET"])
@login_required
def get_incidents():
    incidents = Incident.query.order_by(
        Incident.created_at.desc()
    ).all()

    return {
        "incidents": [
            {
                "id": incident.id,
                "title": incident.title,
                "description": incident.description,
                "priority": incident.priority,
                "status": incident.status,
                "assigned_to": incident.assigned_to,
            }
            for incident in incidents
        ]
    }

# REST API: GET one incident by ID
@app.route("/api/incidents/<int:incident_id>", methods=["GET"])
@login_required
def get_incident(incident_id):
    incident = db.session.get(Incident, incident_id)

    if incident is None:
        return {"error": "Incident not found."}, 404

    return {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "priority": incident.priority,
        "status": incident.status,
        "assigned_to": incident.assigned_to,
    }


# --------------------------------------------------
# REST API: POST create an incident
# --------------------------------------------------

@app.route("/api/incidents", methods=["POST"])
@login_required
def create_incident_api():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "A JSON object is required."}, 400

    title = data.get("title", "")
    description = data.get("description", "")
    priority = data.get("priority", "Medium")

    if not isinstance(title, str) or not isinstance(description, str):
        return {"error": "Title and description must be text."}, 400

    title = title.strip()
    description = description.strip()

    if not title or not description:
        return {"error": "Title and description are required."}, 400

    if priority not in {"Low", "Medium", "High", "Critical"}:
        return {"error": "Invalid priority."}, 400

    incident = Incident(
        title=title,
        description=description,
        priority=priority,
    )

    db.session.add(incident)
    db.session.commit()

    return {
        "message": "Incident created successfully.",
        "id": incident.id,
        "title": incident.title,
        "status": incident.status,
    }, 201


# --------------------------------------------------
# REST API: PATCH update an incident
# Only Admins and Agents can update
# --------------------------------------------------

@app.route("/api/incidents/<int:incident_id>", methods=["PATCH"])
@roles_required("Admin", "Agent")
def update_incident_api(incident_id):
    incident = db.session.get(Incident, incident_id)

    if incident is None:
        return {"error": "Incident not found."}, 404

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return {"error": "A JSON object is required."}, 400

    if "status" in data:
        if data["status"] not in {"Open", "In Progress", "Resolved"}:
            return {"error": "Invalid incident status."}, 400

        incident.status = data["status"]

    if "assigned_to" in data:
        assigned_to = data["assigned_to"]

        if assigned_to is not None and not isinstance(assigned_to, str):
            return {"error": "assigned_to must be text or null."}, 400

        if isinstance(assigned_to, str) and len(assigned_to.strip()) > 100:
            return {"error": "Technician name must be 100 characters or fewer."}, 400

        incident.assigned_to = (
            assigned_to.strip() or None
            if assigned_to is not None
            else None
        )

    db.session.commit()

    return {
        "message": "Incident updated successfully.",
        "id": incident.id,
        "title": incident.title,
        "status": incident.status,
        "assigned_to": incident.assigned_to,
    }




# REST API: DELETE an incident
# Only Admin and Agent users can delete incidents
@app.route("/api/incidents/<int:incident_id>", methods=["DELETE"])
@roles_required("Admin", "Agent")
def delete_incident_api(incident_id):
    incident = db.session.get(Incident, incident_id)

    if incident is None:
        return {"error": "Incident not found."}, 404

    db.session.delete(incident)
    db.session.commit()

    return {
        "message": "Incident deleted successfully.",
        "id": incident_id,
    }


# --------------------------------------------------
# Login and logout
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("home"))

        return "Invalid username or password.", 401

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))



# User registration
@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(username) < 3:
            return "Username must contain at least 3 characters.", 400

        if len(password) < 8:
            return "Password must contain at least 8 characters.", 400

        if password != confirm_password:
            return "Passwords do not match.", 400

        if User.query.filter_by(username=username).first():
            return "Username already exists.", 400

        user = User(username=username, role="Reporter")
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("register.html")

# Admin-only user management page
@app.route("/users")
@roles_required("Admin")
def manage_users():
    users = User.query.order_by(User.username.asc()).all()
    return render_template("users.html", users=users)




# Admin-only: Change a user's role
@app.route("/users/<int:user_id>/role", methods=["POST"])
@roles_required("Admin")
def change_user_role(user_id):
    user = db.session.get(User, user_id)

    if user is None:
        abort(404)

    new_role = request.form.get("role", "")
    allowed_roles = {"Admin", "Agent", "Reporter"}

    if new_role not in allowed_roles:
        abort(400, description="Invalid user role.")

    # Prevent removing the last Admin
    if user.role == "Admin" and new_role != "Admin":
        admin_count = User.query.filter_by(role="Admin").count()

        if admin_count <= 1:
            return "Cannot remove the last Admin account.", 400

    user.role = new_role
    db.session.commit()

    return redirect(url_for("manage_users"))

# --------------------------------------------------
# Run application
# --------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
