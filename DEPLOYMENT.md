# 🚀 MindBloom Deployment Guide

This guide covers deploying **MindBloom** to **Streamlit Community Cloud** (free, instant 1-click hosting), Docker, or any cloud platform.

---

## 🌟 Option 1: Streamlit Community Cloud (Recommended — 100% Free)

Streamlit Community Cloud is the easiest and fastest way to deploy MindBloom.

### Step-by-Step Instructions:

1. **Push your code to GitHub**:
   Ensure all files (`app.py`, `requirements.txt`, `.streamlit/config.toml`, `liquid_chrome.py`, `database.py`, etc.) are committed and pushed to your GitHub repository (e.g. `https://github.com/your-username/mindbloom`).

2. **Log into Streamlit Community Cloud**:
   Go to [share.streamlit.io](https://share.streamlit.io) and sign in with your GitHub account.

3. **Deploy New App**:
   - Click **"New app"** (or **"Create app"**).
   - Select your repository: `your-username/mindbloom`
   - Branch: `main`
   - Main file path: `app.py`
   - Click **"Deploy!"**

4. **Done!**
   Your live application URL will be generated (e.g., `https://mindbloom.streamlit.app`).

> **Note on Database**: MindBloom uses SQLite. On fresh deployment, it automatically provisions the schema and populates default demo data for instant evaluation.

---

## 🐳 Option 2: Docker Container Deployment

MindBloom includes a production-ready `Dockerfile`.

### Build & Run Locally:

```bash
# Build the Docker image
docker build -t mindbloom .

# Run the container on port 8501
docker run -p 8501:8501 mindbloom
```

Open your browser at `http://localhost:8501`.

---

## ☁️ Option 3: Render / Railway / Heroku (via Procfile)

MindBloom includes a standard `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

1. Create a new **Web Service** on Render or Railway.
2. Link your GitHub repository.
3. Set build command to `pip install -r requirements.txt`.
4. Set start command to `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`.

---

## 💻 Option 4: Local Development

```bash
# 1. Clone repository
git clone https://github.com/your-username/mindbloom.git
cd mindbloom

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the Streamlit application
streamlit run app.py
```

---

## 🔑 Demo & Test Credentials

- **Demo Account Email**: `demo@mindbloom.com`
- **Password**: `password123`
- **1-Click Login**: Simply tap the **"🚀 1-Click Demo Login"** button on the sign-in screen.
- **Caregiver PIN**: `1234`
