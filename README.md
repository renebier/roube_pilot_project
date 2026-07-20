
# Lohn-Audit AI Pilot Project
## MAC or slower computer Version
Please self-host ollama in this version it is disabled in the docker compose to save processing power.
Everythings else stays the same
## ENV VARS
> **Note on Environment Variables:**
> `.env` files have been committed to this repository for ease of testing. In a production setup, environment variables must be loaded dynamically and kept out of version control.

---

> ⚠️ **IMPORTANT:**
> Please set `TEAMS_WEBHOOK_URL` in the `src/.env` file before running the application. This is the only variable not committed as it is personally scoped. Refer to the project documentation for instructions on obtaining a Webhook URL.

---

## Getting Started

1. **Navigate to the infrastructure directory:**
```bash
   cd infra/
```

* **NVIDIA GPU:** Ensure `nvidia-container-toolkit` is installed on your host system.
* **AMD / Intel GPU:** Modify `docker-compose.yml` and the `Dockerfile` to configure the appropriate Ollama image variant and device pass-throughs.
* **CPU Fallback:** If GPU pass-through is skipped, Ollama will fall back to CPU execution (inference will be slower).

2. **Prepare the Database:**
Place your MSSQL `.bak` file into the `infra/` directory and rename it to:
```text
bu_erp_data.bak
```


3. **Build and Deploy Containers:**
Run the following command to start both the MSSQL database and the local Ollama container:
```bash
docker compose up --build -d
```

* Automatically restores data from `bu_erp_data.bak`.
* Automatically pulls and initializes `qwen2.5:7b`.
* *Note:* Initial startup may take several minutes due to base image and model downloads.


4. **Set Up Python Environment:**
Navigate to `src/` and install dependencies using `pyproject.toml` (e.g., via [`uv`](https://github.com/astral-sh/uv)):
```bash
cd ../src/
uv sync
```

5. **Run the Pipeline:**
Once dependencies are installed, execute the main application:
``` bash
python main.py
```
