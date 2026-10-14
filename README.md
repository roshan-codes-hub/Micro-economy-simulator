# Algorithmic Micro-Economy Simulator

An in-progress Python project exploring how trading activity and market
rules can shape behaviour in a simulated economy.

The project focuses on building a reliable exchange foundation first,
with the longer-term goal of introducing autonomous trading agents and
studying how their interactions affect market outcomes.

## Project Status

**Work in progress.** This repository represents an evolving prototype,
not a finished economic simulator.

### Current focus

The exchange layer is being developed around core market mechanics such
as:

-   Order validation and order-book operations
-   Portfolio and balance accounting
-   Resource reservations for open orders
-   Partial order fills
-   Trade settlement and reservation updates

Only consider a feature complete if it is present and working in the
current codebase.

### Planned directions

-   Autonomous agents with different trading strategies
-   Simulated economic events and news
-   Experiments involving price movements, bubbles, and other market
    dynamics
-   Visualizations and analysis of simulation outcomes

These are planned extensions and may not yet be implemented.

## Why This Project?

I wanted to explore the engineering behind market simulations rather
than start with AI agents alone. A simulation needs consistent rules for
orders, balances, and settlement before the behaviour of autonomous
traders can be meaningfully studied.

One important design challenge is handling partially filled orders
correctly: the system must distinguish executed quantities from
remaining quantities and keep account balances and reserved resources
consistent.

## Getting Started

The exact setup depends on the current implementation. Once the
project's entry point and dependencies are finalized, add the verified
commands here.

Typical Python setup:

``` bash
git clone <your-repository-url>
cd MicroEconomySimulator
python -m venv .venv
```

Activate the virtual environment:

**Windows PowerShell**

``` powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

``` bash
source .venv/bin/activate
```

Install dependencies only if the repository includes a dependency file:

``` bash
pip install -r requirements.txt
```

Run the project using its actual entry point. For example, if the
repository has a verified `main.py` entry point:

``` bash
python main.py
```

Replace these instructions with the exact commands that work for the
current codebase before treating this README as complete.

## Testing

Run the tests that are present in the repository using the project's
documented test command. Add test instructions here once verified.

Important cases to test include:

-   Valid and invalid orders
-   Orders that fill completely or partially
-   Remaining quantities after partial fills
-   Balance and holdings updates after settlement
-   Release of unused reservations
-   Attempts to spend already-reserved funds

## Repository Structure

The structure may change as the project develops. Document the actual
modules and their responsibilities here once they are stable.

## Limitations

-   The project is under active development.
-   Autonomous agents, LLM integration, economic-event simulation, and
    visual analytics should be considered future work unless implemented
    in the current repository.
-   Results from a simplified simulation should not be interpreted as
    predictions of real-world financial markets.

## Contributing

This is currently a personal learning and development project.

