# Safe Storage Project

This project consists of a Flask API for managing storage rentals and a Django backoffice for administration.

## Safe Storage API (`safe_storage_api/`)

- **Description:** A Flask-based API providing endpoints for managing clients, employees, storage units, rentals, and other related operations.
- **Technology:** Flask, SQLAlchemy, Flask-Migrate.
- **Database:** SQLite (`safe_storage_api/app.db`)
- **Setup & Run:** (Details would typically go here, e.g., how to install dependencies from `safe_storage_api/requirements.txt`, set up environment variables, and run the Flask app using `safe_storage_api/run.py`). Refer to specific documentation within the `safe_storage_api` directory if available.

## Django Backoffice (`backoffice/`)

- **Description:** A Django admin web application providing an administrative interface for the data managed by the Safe Storage API. It operates on the same database (`safe_storage_api/app.db`).
- **Technology:** Django.

### Backoffice Setup

1.  **Prerequisites:**
    *   Python 3.x
    *   Ensure the Safe Storage API's database (`safe_storage_api/app.db`) exists, as the backoffice uses it.

2.  **Install Dependencies:**
    The main `safe_storage_api/requirements.txt` file includes Django. Install all dependencies:
    ```bash
    pip install -r safe_storage_api/requirements.txt
    ```

3.  **Run Django Migrations:**
    Navigate to the `backoffice` directory and run migrations. This sets up Django's own database tables (for admin, sessions, etc.). It will not affect the tables already managed by the Flask API's Alembic migrations because the Django models for those tables are set with `Meta.managed = False`.
    ```bash
    cd backoffice
    python manage.py migrate
    cd .. 
    ```
    *(Note: `cd ..` is added to return to the root for subsequent commands if any, or adjust as needed depending on where further commands are expected to be run from.)*

4.  **Create a Superuser:**
    To access the Django admin interface, you need an administrator account.
    ```bash
    cd backoffice
    python manage.py createsuperuser
    cd ..
    ```
    Follow the prompts to set a username, email, and password.

### Running the Backoffice

1.  **Navigate to the `backoffice` directory:**
    ```bash
    cd backoffice
    ```

2.  **Start the Django development server:**
    ```bash
    python manage.py runserver
    ```
    The backoffice will typically be accessible at `http://127.0.0.1:8000/admin/`.

3.  **Login:**
    Use the superuser credentials created during the setup.
