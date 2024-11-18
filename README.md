### Authzed Example: Getting Started

#### Overview

This repository provides a simple example of how to deploy the **Authzed** service using Docker. It also includes sample Python scripts to demonstrate interactions with the service.

---

### Prerequisites

- **Docker** and **Docker Compose** installed on your system.
- Basic understanding of Python and Docker workflows.

---

### Quick Start

#### 1. Deploy the Authzed Service

1. Copy the example environment file:
   ```bash
   cp example.env .env
   ```
2. Build the Docker containers:
   ```bash
   docker-compose build
   ```
3. Start the Authzed service:
   ```bash
   docker-compose up
   ```

#### 2. Customize the Schema (Optional)

If you need to modify the schema:
- Edit the file: `docker/authzed/schema.yaml`.
- Redeploy the containers using the steps above.

#### 3. Test Interaction with Authzed

Run one of the provided Python scripts to test the service:

- For asynchronous interaction:
  ```bash
  python authzed_async_sample.py
  ```
- For synchronous interaction:
  ```bash
  python authzed_sync_sample.py
  ```

---

### Notes

- Ensure your `.env` file is correctly configured for your environment.
- Refer to the official [Authzed Documentation](https://docs.authzed.com) for further details on schema design and advanced configurations.

---

Happy coding! 🎉
