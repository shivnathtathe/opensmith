# Contributing

Thanks for helping improve opensmith. This project aims to stay small, local-first, and easy to install.

## Local Setup

```bash
git clone https://github.com/shivnathtathe/opensmith.git
cd opensmith
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest tests/ -v
```

All changes should keep the test suite passing. Add tests for new behavior, bug fixes, and public API changes.

## Development Guidelines

- Keep the package local-first. Do not add cloud services or external telemetry.
- Do not introduce non-SQLite storage backends.
- Lazy import optional LLM/vector database clients.
- Keep public APIs typed and simple.
- Avoid adding required dependencies unless they are essential.

## Pull Requests

Before opening a pull request:

- Run `pytest tests/ -v`.
- Update documentation when behavior changes.
- Keep changes focused and easy to review.
- Include a clear summary of the problem and solution.

## Issues

Use the bug report template for reproducible problems and the feature request template for proposed enhancements.
