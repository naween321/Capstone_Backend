# 🚀 LifeLog

LifeLog is a Dockerized Django-based application managed using **uv** for Python dependency management and **Make** for command orchestration.

This guide explains how to set up the project locally from scratch.

---

# 📌 Prerequisites

Before starting, make sure the following tools are installed:

---

## 1️⃣ Docker

Docker is used to containerize and run the application.

Install Docker:  
https://docs.docker.com/get-docker/

Verify installation:

```bash
docker --version
```

---

## 2️⃣ Make

Make is used to execute predefined commands from the `Makefile`.

### Mac
```bash
brew install make
```

### Ubuntu/Debian
```bash
sudo apt install make
```

### Windows (Use Powershell)
```powershell
choco install make
```

Verify installation:

```bash
make --version
```

---

## 3️⃣ uv (Python Package Manager)

uv is used for fast and reproducible dependency management.

Install uv:  
https://docs.astral.sh/uv/getting-started/installation/

Quick Install:  
Do this on your global environment
```
pip install uv
```

Verify installation:

```bash
uv --version
```

---

# 🛠️ Project Setup

---

## 1️⃣ Clone the Project

```bash
git clone <your-repository-url>
cd <project_folder>
```

---

## 2️⃣ Create environment using uv

Create a virtual environment:

```bash
uv venv
```

Activate the virtual environment:

### Mac/Linux
```bash
source .venv/bin/activate
```

### Windows
```powershell
.venv\Scripts\activate
```


---

## 3️⃣ Configure Environment Variables

### Create `.env` file in the root directory

```bash
cp .env.example .env
```

Update values inside `.env` as needed.

---

### Create `env.py` inside:

```
LifeLog/settings/env.py
```

Copy content from:

```
LifeLog/settings/env.example.py
```

Modify values according to your local setup.

---

### Set up Firebase (Push Notifications)

The backend uses Firebase Cloud Messaging (FCM) to send push notifications.
A Firebase service account key file is required.

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Select the **lifelog-capstone** project
3. Navigate to **Project Settings > Service accounts**
4. Click **Generate new private key** and download the JSON file
5. Rename it to `serviceAccountKey.json`
6. Place it in the project root directory (`Capstone_Backend/serviceAccountKey.json`)

> **Note:** This file is listed in `.gitignore` and must never be committed.
> The path is configured in `LifeLog/settings/base.py`.

---

# 🐳 Docker & Database Setup

All operational commands are defined inside the `Makefile`.

---

## 4️⃣ Create Migration Files

```bash
make dev-makemigrations
```

---

## 5️⃣ Apply Migrations

```bash
make dev-migrate
```

---

## 6️⃣ Build Docker Container

```bash
make dev-build
```

---

## 7️⃣ Run the Application

```bash
make dev-up
```

---

# 🌐 Access the Application

Once running:

| Service | URL | Port |
|----------|------|------|
| Application | http://localhost:8001 | 8001 |
| Database (Local Web Access) | http://localhost:8081 | 8081 |

---

# 📂 Important Project Structure

```
LifeLog/
│
├── .env
├── serviceAccountKey.json    # Firebase credentials (gitignored)
├── Makefile
├── docker
    ├── lifelog_dev
│       ├── docker-compose.yml
│       └── Dockerfile
│       └── entrypoint.sh
├── pyproject.toml
├── uv.lock
│
└── LifeLog/
    └── settings/
        ├── env.py
        └── env.example.py
```

---

# 🧩 Useful Commands Summary

| Task | Command |
|------|----------|
| Create migrations | make dev-makemigrations |
| Apply migrations | make dev-migrate |
| Build container | make dev-build |
| Run container | make dev-up |
| Stop container | docker compose down |

---

# ⚠️ Notes

- Ensure Docker Desktop is running before executing build or up commands.
- Ports used:
  - Application: **8001**
  - Database Web Access: **8081**
- If ports are already in use, update them in `docker-compose.yml`.
- Always activate the virtual environment before running `uv` commands.

---

# ✅ Setup Complete

**LifeLog** application should now be running locally inside Docker.