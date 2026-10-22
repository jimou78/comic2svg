# Contributing to comic2svg

Thank you for your interest in contributing to **comic2svg**! We welcome all contributions, including bug reports, new presets, feature requests, documentation improvements, and pull requests.

---

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jimou78/comic2svg.git
   cd comic2svg
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies in editable mode:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify the installation:**
   ```bash
   comic2svg --help
   pytest
   ```

---

## Code Style & Guidelines

- **Formatting & Linting**: We use [Ruff](https://github.com/astral-sh/ruff) for linting and code formatting. Run:
  ```bash
  ruff check .
  ```
- **Type Annotations**: All public functions should have descriptive type hints.
- **Tests**: Write unit tests for new features in the `tests/` directory.

---

## Pull Request Guidelines

1. Fork the repo and create your branch from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Make your changes and ensure all tests pass:
   ```bash
   pytest
   ruff check .
   ```
3. Commit your changes with clear, descriptive commit messages.
4. Push to your fork and submit a Pull Request.

---

## License

By contributing to comic2svg, you agree that your contributions will be licensed under the [MIT License](LICENSE).
