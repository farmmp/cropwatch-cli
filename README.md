# cropwatch-cli

> CLI tool to fetch and visualize USDA crop progress reports from the terminal

---

## Installation

```bash
pip install cropwatch-cli
```

Or install from source:

```bash
git clone https://github.com/youruser/cropwatch-cli.git
cd cropwatch-cli
pip install .
```

---

## Usage

Fetch the latest crop progress report:

```bash
cropwatch fetch --crop corn --state iowa
```

Visualize progress as a chart in the terminal:

```bash
cropwatch chart --crop soybeans --year 2024
```

List available crops and states:

```bash
cropwatch list --crops
cropwatch list --states
```

**Example output:**

```
Iowa Corn Progress — Week 32, 2024
Planted:     ████████████████████  98%
Emerged:     ███████████████████   95%
Silking:     ██████████████        72%
Dough:       ████████              41%
```

---

## Requirements

- Python 3.8+
- `requests`, `rich`, `click`

---

## License

This project is licensed under the [MIT License](LICENSE).