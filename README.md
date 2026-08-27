<h1 align="center">
  <img src="./public/favicon.ico" alt="Cortex Data icon" width="28">&nbsp;
  Cortex Data: AI-powered Data Visualization
</h1>

<p align="center">
  🪄 Explore data with visualizations, powered by AI agents.
</p>

<p align="center">
  <a href="https://pypi.org/project/data_formulator/"><img src="https://img.shields.io/pypi/v/data_formulator.svg?label=pypi%3A%20data_formulator" alt="PyPI"></a>&ensp;
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
</p>

## Why Cortex Data?

Working with data is hard for two simple reasons:

1. **Data lives everywhere.** Connecting agents to files, databases,
   warehouses, and BI tools takes time. It is even harder when agents start
   answering before the relationships between data sources are clear.
2. **Questions evolve as you explore.** Each answer can lead to follow-up
   questions, comparisons, and new directions. A long chat history makes it
   hard to see where you are and how you got there.

Cortex Data provides one visual workspace for exploring and analyzing data:

1. **Data connectors** give agents a common way to connect to different data
   sources — files, PostgreSQL, MySQL, SQL Server, Oracle, and more — and
   maintain a data memory to remember the relationships between them.
2. **Data Threads** let you branch into different questions, compare paths,
   and use visualizations to discover deeper insights without losing context.
3. **Chat IA** (`/chat-ia`) gives non-technical users a single-screen,
   conversational way to ask questions in natural language and read the
   answer — no chart-building UI to learn.

## What's in this fork

Cortex Data started as a fork of Microsoft's open-source [Data
Formulator](https://github.com/microsoft/data-formulator) (MIT licensed —
see [LICENSE](LICENSE) for the original copyright notice) and has since
diverged with its own features:

- Full rebrand (name, logo, typography — Public Sans throughout)
- Portuguese (pt-BR) localization alongside English and Chinese
- An Oracle Database connector (SPJQ probe compilation, thin-mode driver)
- `/chat-ia`, a standalone simplified chat interface for non-technical users
- SQL query transparency: every live-database answer shows the exact SQL
  that ran, with a copy button — not just a trust-me result
- Per-identity LLM usage/cost tracking
- Production deploy under Gunicorn + systemd instead of the Flask dev server

See [CHANGELOG.md](CHANGELOG.md) for the upstream release history this fork
started from.

## Get Started

- **Option 1: Install via uv (recommended)**

  [uv](https://docs.astral.sh/uv/) is an extremely fast Python package manager. If you have uv installed, you can run Cortex Data directly without any setup:

  ```bash
  uvx data_formulator
  ```

  Run `uvx data_formulator --help` to see all available options, such as custom port, sandboxing mode, and data storage location.

- **Option 2: Install via pip**

  Use pip for installation (recommend: install it in a virtual environment).

  ```bash
  pip install data_formulator # install
  python -m data_formulator # run
  ```

  Cortex Data will be automatically opened in the browser at [http://localhost:5567](http://localhost:5567).

- **Option 3: Run with Docker**

  ```bash
  docker compose up --build
  ```

  Open [http://localhost:5567](http://localhost:5567) in your browser. To stop, press `Ctrl+C` or run `docker compose down`.

- **Option 4: Working as developer**

  You can build Cortex Data locally and develop your own version. Check out details in [DEVELOPMENT.md](DEVELOPMENT.md).

## Using Cortex Data

Start with the data you already have: upload CSV, TSV, Excel, JSON, screenshots,
or text; connect to databases and data platforms; or ask the analyst to find and
load the data you need. The analyst can discover sources, clarify your request,
propose a loading plan, and let you review the data before adding it to the
workspace.

Continue the conversation in the **Data Thread**. Ask questions in
natural language and follow the reasoning through explanations, tables, and
editable charts in one history. Refine a result directly, branch from any
earlier step to explore an alternative, or delegate the next investigation to
the analyst. When the analysis is ready, compose the results into a report to
share.

## Contributing

This is a private fork under active development. If you have access to the
repository and want to contribute, open an issue or pull request — there's no
CLA or formal process yet for a single-maintainer project at this stage.

## License & Attribution

Cortex Data is a fork of Microsoft's open-source [Data
Formulator](https://github.com/microsoft/data-formulator), licensed under the
MIT License. The original copyright notice is preserved in
[LICENSE](LICENSE) as required by the license terms. Any use of third-party
trademarks or logos is subject to those third parties' own policies.
