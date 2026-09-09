# 🌸 MindBloom

**AI-powered cognitive gaming platform for elderly users** — an SIH internal hackathon prototype.

> ⚠️ **Disclaimer:** MindBloom is an educational prototype built for a hackathon. It does **not** diagnose, prevent, cure, or treat dementia or any medical condition. It is a simple, friendly cognitive engagement and brain-training tool only.

---

## ✨ What's Inside

- 5 cognitive games (Memory Match, Number Memory, Word Recall, Pattern Recognition, Daily Quiz)
- An explainable adaptive-difficulty engine
- English / Hindi / Kannada support
- Browser-based Read Aloud (text-to-speech)
- Daily reminder settings
- A caregiver dashboard with Plotly charts
- Large-font, high-contrast, elderly-friendly UI
- Local SQLite storage (works fully offline when run locally)

---

## 📁 Project Structure

```
mindbloom/
│
├── app.py                # Main Streamlit app (UI + navigation)
├── database.py            # SQLite setup and data access functions
├── adaptive_engine.py     # Adaptive difficulty logic
├── translations.py        # English / Hindi / Kannada text
├── games.py                # Game content generators & scoring
├── voice.py                # Browser text-to-speech helper
├── utils.py                 # Styling, streaks, achievements, helpers
├── requirements.txt
├── README.md
├── .gitignore
└── assets/
    └── logo.png            # (optional) add your own logo here
```

---

## 🖥️ Windows Installation (Step by Step)

1. **Install Python** (if not already installed)
   - Download from [python.org](https://www.python.org/downloads/) (3.10+ recommended)
   - During install, check **"Add Python to PATH"**

2. **Open a terminal / Command Prompt** in the project folder
   ```
   cd path\to\mindbloom
   ```

3. **Create a virtual environment**
   ```
   python -m venv venv
   ```

4. **Activate the virtual environment**
   ```
   venv\Scripts\activate
   ```

5. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

6. **Run the app**
   ```
   streamlit run app.py
   ```

7. Your browser should open automatically at `http://localhost:8501`. If not, open that link manually.

---

## 🧑‍💻 VS Code Steps

1. Open VS Code → **File → Open Folder** → select the `mindbloom` folder.
2. Install the **Python extension** (by Microsoft) from the Extensions tab if you don't have it.
3. Open a new terminal: **Terminal → New Terminal**.
4. Select your virtual environment as the Python interpreter:
   - Press `Ctrl+Shift+P` → type `Python: Select Interpreter` → choose the `venv` one.
5. In the VS Code terminal, run:
   ```
   streamlit run app.py
   ```
6. Edit any `.py` file and save — Streamlit will offer to "Rerun" automatically in the browser tab.

---

## 🔧 Git Commands

```bash
# Initialize a new repository (only once)
git init

# Add all project files
git add .

# Commit your changes
git commit -m "Initial commit: MindBloom hackathon prototype"

# Set the main branch name
git branch -M main
```

---

## ☁️ GitHub Upload Instructions

1. Go to [github.com](https://github.com) and create a **New Repository** (e.g. `mindbloom`).
   - Do **not** initialize it with a README (we already have one).
2. Copy the repository URL GitHub gives you, then run:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/mindbloom.git
   git push -u origin main
   ```
3. Refresh your GitHub repository page — your files should now appear.

---

## 🚀 Streamlit Community Cloud Deployment

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
2. Click **"New app"**.
3. Select:
   - **Repository:** `YOUR_USERNAME/mindbloom`
   - **Branch:** `main`
   - **Main file path:** `app.py`
4. Click **Deploy**.
5. Wait a minute or two while it installs `requirements.txt` and launches.
6. Your app will be live at a URL like `https://your-app-name.streamlit.app`.

> **Note on offline vs. cloud mode:** Running MindBloom locally (`streamlit run app.py`) means all game content and SQLite data work fully offline once the app and dependencies are installed. Streamlit Community Cloud, however, requires an internet connection to reach the hosted app — it does **not** provide full offline operation. Each deployment (local or cloud) keeps its own separate local `mindbloom.db` file.

---

## 🐞 Troubleshooting

| Problem | Solution |
|---|---|
| `streamlit: command not found` | Make sure your virtual environment is activated, then re-run `pip install -r requirements.txt` |
| Blank page / app won't load | Check the terminal for errors; make sure you're running `streamlit run app.py` from inside the `mindbloom` folder |
| Database errors on first run | Delete `mindbloom.db` if it exists and restart the app — `database.py` will recreate it automatically |
| Charts not showing on Caregiver Dashboard | Click **"Load Demo Data"** on the Caregiver Dashboard to generate sample activity for the presentation |
| Voice / Read Aloud not working | This depends on your browser supporting the Web Speech API. Chrome and Edge generally work best. Voice is optional — all content is also shown as text |
| Port already in use | Run `streamlit run app.py --server.port 8502` to use a different port |
| Changes not appearing | Save the file, then click "Rerun" in the browser, or restart `streamlit run app.py` |

---

## 🎬 Suggested SIH Demo Flow

1. Open MindBloom → create/select a profile
2. Switch language to Hindi or Kannada in Settings
3. Play **Memory Match** → show score & encouraging feedback
4. Notice the adaptive engine's explanation when difficulty changes
5. Play a second game (e.g. Daily Quiz)
6. Open **Progress** → show streak, achievements, weekly chart
7. Open **Caregiver Dashboard** → PIN `1234` → click **Load Demo Data** → show charts
8. Open **Reminders** → show reminder settings
9. Open **Settings** → demonstrate Extra Large font + High Contrast mode
10. Demonstrate **Read Aloud** on the Home page

---

## 🔒 Prototype Notes

- This is a **hackathon prototype**, not a production medical or security system.
- No medical records or sensitive health information are collected or stored.
- The caregiver login uses a simple demo PIN (`1234`) for demonstration purposes only.
- All encouraging messages are intentionally positive — the app never shows negative or frightening feedback for incorrect answers.
