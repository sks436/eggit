# EGGIT - Hatch the Habit of Learning Better

Welcome to **EGGIT**! This is a simple Flask web application designed to help users hatch the habit of learning better through personalized learning resources, scheduling, and user management. Built with **SQLite** as the database, this app includes basic user authentication and a clean interface for managing learning sessions.

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/P202U/Eggit---Hatch-the-habit-of-learning.git
cd EGGIT
```

### 2. Setup Configuration

To configure the application, you need to set up the environment variables in a .env file. Follow these steps:

1. **Rename the `.env.sample` File**

   - In the project directory, you’ll find a file named `.env.sample`.
   - Rename it to `.env`.

   ```bash
   mv .env.sample .env
   ```

   This will create a new `.env` file that will be used by Flask to load environment variables.

2. **Set Up Your Email Configuration (Optional)**

   If you want to use email functionality (password reset emails), configure the following:

   - **EMAIL_ADDRESS**: Enter your email address (e.g., a Gmail account).
   - **EMAIL_PASSWORD**: If you're using Gmail and have 2-Step Verification enabled, create an [App Password ](https://myaccount.google.com/apppasswords)
     instead of using your Gmail password.

### 3. Set up a virtual environment

If you haven't already created a virtual environment, do so:

```bash
python -m venv venv
```

### 4. Activate the virtual environment

- For **macOS/Linux**

  ```bash
  source venv/bin/activate
  ```

- For **Windows** (using VS Code terminal)
  ```bash
  venv/scripts/Activate
  ```

### 5. Install the dependencies

```bash
  pip install -r requirements.txt
```

### 6. Run the app

```bash
flask run
```

### 7. Admin login details

**Login ID**: admin123

**Password**: admin123

<kbd>Note</kbd> **Populate your db by creating users**
