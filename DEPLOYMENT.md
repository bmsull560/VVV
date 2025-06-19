# Deployment Guide

This document provides guidance for deploying the B2BValue application securely and effectively.

## Secure Configuration

### SECRET_KEY Management

The `SECRET_KEY` is critical for securing session data and cryptographic signing. It **must not** be hardcoded in the application or committed to version control.

**Configuration:**

1.  **Environment Variable:** The application loads the `SECRET_KEY` from an environment variable named `B2BVALUE_SECRET_KEY`.
2.  **Generation:** Generate a strong, random key. A good way to do this is using Python's `secrets` module:
    ```python
    import secrets
    print(secrets.token_hex(32))
    ```
3.  **Setting the Variable:** Set the `B2BVALUE_SECRET_KEY` environment variable in your production environment. The method for setting environment variables depends on your deployment platform (e.g., Docker, Kubernetes, PaaS provider settings).

    *   **Example (Linux/macOS shell):**
        ```bash
        export B2BVALUE_SECRET_KEY='your_generated_strong_secret_key'
        ```
    *   **Example (Windows PowerShell):**
        ```powershell
        $Env:B2BVALUE_SECRET_KEY = 'your_generated_strong_secret_key'
        ```
    *   **Docker:** Use the `-e` flag or a `.env` file with `docker run`, or define it in your `docker-compose.yml`.
    *   **Kubernetes:** Use Secrets to store and manage the `SECRET_KEY` and mount it as an environment variable in your pods.

**Security Best Practices:**

*   **Uniqueness:** Use a unique `SECRET_KEY` for each environment (development, staging, production).
*   **Rotation:** Consider rotating the `SECRET_KEY` periodically as part of your security policy.
*   **Access Control:** Limit access to where the `SECRET_KEY` is stored and configured.

If the `B2BVALUE_SECRET_KEY` environment variable is not set, the application will raise a `RuntimeError` on startup to prevent insecure operation.

### PostgreSQL Database Connection

The application requires a PostgreSQL database for persistent storage, including user authentication.

**Environment Variables:**

Configure the following environment variables to connect to your PostgreSQL instance:

*   `POSTGRES_USER`: Username for the PostgreSQL database.
*   `POSTGRES_PASSWORD`: Password for the PostgreSQL user.
*   `POSTGRES_HOST`: Hostname or IP address of the PostgreSQL server (e.g., `localhost` or an IP).
*   `POSTGRES_PORT`: Port number for the PostgreSQL server (default is `5432`).
*   `POSTGRES_DB`: Name of the PostgreSQL database to use.

**Example (Linux/macOS shell):**
```bash
export POSTGRES_USER='your_db_user'
export POSTGRES_PASSWORD='your_db_password'
export POSTGRES_HOST='localhost'
export POSTGRES_PORT='5432'
export POSTGRES_DB='b2bvalue_db'
```

**Database Schema Migrations:**

Database schema changes are managed via SQL scripts in the `migrations/` directory. Apply these migrations to your database before running the application for the first time or after an update that includes schema changes.

For example, to apply the initial user table migration, you would run the `migrations/001_create_users_table.sql` script against your PostgreSQL database using a tool like `psql`:

```bash
psql -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB -f migrations/001_create_users_table.sql
```

Ensure the database user has permissions to create tables and extensions (like `pgcrypto` if used for `gen_random_uuid()`).
