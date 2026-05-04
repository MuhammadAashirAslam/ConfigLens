# Contributing to ConfigLens

Thank you for contributing to ConfigLens! ConfigLens is built to detect configuration debt and drift across DevOps configurations with zero network calls and deterministic static analysis.

## Development Setup

1. Clone the repository and install the development dependencies:
   ```bash
   git clone https://github.com/MuhammadAashirAslam/ConfigLens.git
   cd ConfigLens
   pip install -e ".[dev]"
   ```

2. Run the test suite:
   ```bash
   pytest -v
   ```

## Commit & Development Guidelines

- **Atomic Commits**: Keep commits small and focused on one logical unit of change.
- **Commit Messages**: Use Conventional Commits (`feat(scope): ...`, `fix(scope): ...`, `test(scope): ...`).
- **Tests**: Every new rule or feature must include unit tests and corresponding test fixtures.
- **Zero Network**: The core scanner must never make network calls or invoke external processes during scans.
