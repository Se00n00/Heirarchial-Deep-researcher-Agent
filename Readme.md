<div align="center" ><img src="artifacts/hydra.png"></div>


<div align="center">

![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)
![Research Agent](https://img.shields.io/badge/Agent-Hierarchical%20Research-purple)
![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-orange)
![Status](https://img.shields.io/badge/Status-Active-success)
![License](https://img.shields.io/github/license/Se00n00/Heirarchial-Deep-researcher-Agent)
![Reproducible](https://img.shields.io/badge/Reproducible-Yes-success)

</div>

---

<div align="center">

# HyDRA: Hierarchical Deep Researcher Agent
</div>


## Content Navigation

* [Project Overview](#hierarchical-deep-research-agent)
* [Architecture Overview](#architecture)
* [Project Structure](#project-structure)
* [Benchmark Results](#benchmark-results)
* [Reuirements](#requirements)
* [Setup and Reproducibility](#setup-and-reproducibility)
* [Evaluation](#evaluation)
* [Project Status](#status)

---

## Requirements

### API Keys

The following environment variables are required to run or evaluate the agent:

| Variable         | Description                                       |
| ---------------- | ------------------------------------------------- |
| `GROQ_API_KEY`   | Primary agent inference                           |
| `GROQ_API_KEY_2` | Context manager (token-efficient planning)        |
| `GROQ_BASE_URL`  | Groq API base URL                                 |
| `HF_TOKEN`       | Hugging Face token (required for evaluation only) |

Example:

```bash
    export GROQ_API_KEY=your_key_here
    export GROQ_API_KEY_2=your_key_here
    export GROQ_BASE_URL=https://api.groq.com
    export HF_TOKEN=your_hf_token_here
```
---
## Setup and Reproducibility


This mutli-agent is **fully reproducible** and can be run in an isolated virtual environment with no cached dependencies.

### Quickstart [Run the Agent]

```bash
    # Create and activate a virtual environment
    python -m venv .venv
    source .venv/bin/activate

    # Set required environment variables
    export GROQ_API_KEY
    export GROQ_API_KEY_2
    export GROQ_BASE_URL

    # Install dependencies without caching (low disk usage)
    python -m pip install --no-cache-dir -r requirements.txt

    # Run the agent
    python src/agent.py
```

---
## Evaluation

Evaluation scripts benchmark the agent on established datasets.


### Run Evaluation

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Set environment variables
export GROQ_API_KEY
export GROQ_API_KEY_2
export GROQ_BASE_URL
export HF_TOKEN

# Install dependencies without caching
python -m pip install --no-cache-dir -r requirements.txt

# Run evaluation
python Evaluation_Suite/evaluation_<dataset>.py <evaluation_name> --time [sleep_seconds]
```

**Parameters**

* `<dataset>`: `gaia`, `simpleQA`, `hle`
* `<evaluation_name>`: Unique identifier for the run
* `--time` *[optional]*: Sleep interval between examples (rate-limit control)

---
## Status

- This project is fully functional. Core agent capabilities are stable and usable.
- Evaluation on benchmarks are currently in progress.

---