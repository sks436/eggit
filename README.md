# EGGIT - Hatch the Habit of Learning Better

Welcome to **EGGIT**! This is a simple Flask web application designed to help users hatch the habit of learning better through personalized learning resources, scheduling, and user management. Built with **SQLite** as the database, this app includes basic user authentication and a clean interface for managing learning sessions.

## Setup Instructions

### 1. Clone the repository:

```bash
git clone https://github.com/yourusername/EGGIT.git
cd EGGIT
```

### 2. Set up a virtual environment:

If you haven't already created a virtual environment, do so:

```bash
python3 -m venv venv
```

### 3. Activate the virtual environment:

- For **macOS/Linux**:

  ```bash
  source venv/bin/activate
  ```

- For **Windows** (using Git Bash or WSL):
  ```bash
  source venv/Scripts/activate
  ```
- For **Windows** (using Command Prompt):
  ```bash
  venv\Scripts\activate.bat
  ```
- For **Windows** (using PowerShell):
  ```bash
  venv\Scripts\Activate.ps1
  ```

### 4. Install the dependencies:

```bash
  pip install -r requirements.txt
```

### 5. Configure your environment variables:

- Copy the `.env.example` to `.env`:

```bash
cp .env.example .env
```

- Open `.env` and update the values for `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, and other environment variables as needed.

### 6. Run the app:

```bash
python app.py
```

### 7. Deactivate the virtual environment (when done):

Once you’re done, simply deactivate the virtual environment:

```bash
deactivate
```
