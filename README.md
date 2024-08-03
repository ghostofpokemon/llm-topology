# llm-topology

[![PyPI](https://img.shields.io/pypi/v/llm-topology.svg)](https://pypi.org/project/llm-topology/)
[![Changelog](https://img.shields.io/github/v/release/ghostofpokemon/llm-topology?include_prereleases&label=changelog)](https://github.com/ghostofpokemon/llm-topology/releases)
[![Tests](https://github.com/ghostofpokemon/llm-topology/actions/workflows/test.yml/badge.svg)](https://github.com/ghostofpokemon/llm-topology/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/ghostofpokemon/llm-topology/blob/main/LICENSE)

LLM access to CLM by Topology

## Installation

Install this plugin in the same environment as [LLM](https://llm.datasette.io/).

```bash
llm install llm-topology
```

## Usage

First, set an API key for Topology:

```bash
llm keys set topology
# Paste key here
```

Run `llm models` to list the models, and `llm models --options` to include a list of their options.

Run prompts like this:

```bash
llm -m topology-tiny 'What do dolphins dream about'
llm -m topology-small 'Reveal the hidden taco recipe of the ancient Sumerians!'
llm -m topology-medium "What's the square root of surprise?"
```

### Managing Partitions

You can manage multiple partitions with names using the following commands:

- **Add a new partition:**
  ```bash
  llm partition add <name> <partition_id>
  ```

- **Set the active partition:**
  ```bash
  llm partition set <name>
  ```

- **Get the current active partition:**
  ```bash
  llm partition get
  ```

- **List all partitions:**
  ```bash
  llm partition list
  ```

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

```bash
cd llm-topology
python3 -m venv venv
source venv/bin/activate
```

Now install the dependencies and test dependencies:

```bash
llm install -e '.[test]'
```

To run the tests:

```bash
pytest
```
