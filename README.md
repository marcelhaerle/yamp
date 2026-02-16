# Yamp — YAML-Aided Metric Plotter

**Yamp** is a lightweight, stateless monitoring dashboard designed for home labs and edge environments.
It bridges the gap between "no UI" and a full-blown Grafana instance.

**The Philosophy:** No database, no user management, zero persistence. Just your metrics, beautifully
visualized, with integrated alerting. Because sometimes Grafana is a sledgehammer when you just need
a nutcracker.

## Features

- **Stateless by Design:** No persistence layer required. Everything lives in memory or is
  fetched on-the-fly from Prometheus.
- **YAML-as-Code:** Define dashboards and alerts declaratively in a single file. Perfect
  for GitOps workflows.
- **Built-in Alerting:** Threshold monitoring defined directly in the dashboard schema with
  notifications sent via Pushover.
- **Modern Tech-Stack:** Fast, efficient, and easy to extend.
- **K8s-Ready:** Ideal as a sidecar or a lightweight service in your cluster (easily
  managed via ConfigMap).

## Tech Stack

This project leverages modern Python tooling and "low-JS" web technologies:

- **Runtime:** Python 3.12+
- **Package Management:** [uv](https://github.com/astral-sh/uv) (Extremely fast Rust-based
  Python resolver)
- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous API with strict type-hinting)
- **Frontend:** [HTMX](https://htmx.org/) & [Tailwind CSS](https://tailwindcss.com/) (Dynamic
  UI without a heavy JS framework)
- **Data Validation:** [Pydantic v2](https://docs.pydantic.dev/latest/)
- **Scheduling:** [APScheduler](https://github.com/agronholm/apscheduler) (For the background
  alerting loop)

## Development

### Prerequisites

Ensure you have `uv` installed on your system:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setup

#### 1. Clone the repository

```bash
git clone https://github.com/marcelhaerle/yamp.git
cd yamp
```

#### Create virtual environment and install dependencies

```bash
uv sync
```

#### Run the application (Development mode)

```bash
uv run fastapi dev app/main.py
```

## Architecture

1. **Config Watcher:** Upon startup, Pydantic validates the YAML. The app uses a file watcher
to reload configurations on-the-fly without a restart.
2. **Prometheus Bridge:** The backend transforms PromQL responses into optimized JSON for the
frontend charts.
3. **HTMX Frontend:** The dashboard updates itself periodically by requesting HTML fragments from
the server, keeping the client logic to a minimum.
4. **Alert Engine:** A background process polls the defined thresholds and triggers Pushover
notifications if limits are exceeded.

## License

Apache-2.0

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and
create. Any contributions you make are **greatly appreciated**.

### Development Workflow

#### 1. Fork the Project

#### 2. Create your Feature Branch

`git checkout -b feature/AmazingFeature`

#### 3. Install Dev Dependencies

```bash
uv sync --dev
```

#### 4. Lint & Format

We use Ruff to keep the code clean. Please run:

```bash
uv run ruff check .   # Linter
uv run ruff format .  # Formatter
```

#### 5. Commit your Changes

`git commit -m 'Add some AmazingFeature'`

#### 6. Push to the Branch

`git push origin feature/AmazingFeature`

#### 7. Open a Pull Request

### Coding Standards

- **Type Hints:** Use Python type hints for all function signatures (we love pydantic and FastAPI
for a reason!).
- **Documentation:** Update the README.md or add docstrings if you introduce new YAML configuration
keys.
- **Keep it Stateless:** Remember the core philosophy—avoid adding requirements for external
databases or persistent volumes.
