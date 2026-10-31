# IncidentHub — Incident Management System

A Flask-based incident management application for tracking, assigning, and managing IT incidents with role-based access control.

## Features

- User authentication and role-based access control
- Admin, Agent, and Reporter roles
- Incident tracking and management
- REST API
- SQLite database
- Docker containerization
- Persistent database storage

## Technology Stack

- Python
- Flask
- Flask-Login
- Flask-SQLAlchemy
- SQLite
- Docker
- Ubuntu Linux

## Docker Hub

Docker image: [`itsurvey6/incidenthub:1.0`](https://hub.docker.com/r/itsurvey6/incidenthub)

Pull the image:

```bash
docker pull itsurvey6/incidenthub:1.0
```

## Deployment with Docker

Generate a secure secret key:

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

Create a persistent directory for the database:

```bash
mkdir -p "$HOME/incidenthub-data"
```

Run the container, replacing `YOUR_GENERATED_SECRET_KEY` with the generated value:

```bash
docker run -d \
  --name incidenthub \
  --restart unless-stopped \
  -p 5000:5000 \
  -e SECRET_KEY='YOUR_GENERATED_SECRET_KEY' \
  -v "$HOME/incidenthub-data:/app/instance" \
  itsurvey6/incidenthub:1.0
```

Access the application at:

`http://YOUR_SERVER_IP:5000`

For local testing, use `http://localhost:5000`.

## Database Persistence

The SQLite database is stored in a host directory mounted into the container. This allows the database to persist when the container is recreated, provided the host directory is retained.

## Security Notes

- Use a strong, unique secret key.
- Change or disable any demo accounts before deployment.
- Do not expose the application publicly without appropriate HTTPS, firewall, and production security configuration.
- Back up the database regularly.

## Author

GitHub: [itsurvey6-lab](https://github.com/itsurvey6-lab)

Docker Hub: [itsurvey6](https://hub.docker.com/u/itsurvey6)