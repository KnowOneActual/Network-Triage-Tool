# Contributing to Network Triage Tool

First off, thank you for considering contributing to the Network Triage Tool\! It's people like you that make open-source tools better for everyone.

This project is currently a **Work in Progress**, so there are plenty of opportunities to help out—whether it's fixing bugs, adding support for Linux/Windows, or improving the UI.

## 🛠 Getting Started

To start contributing, you'll need to get the project running locally.

1.  **Fork and Clone** the repository to your local machine.
2.  **Set up your environment** (Python 3.7+ required):
    ```bash
    # Create a virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # Install dependencies
    pip install -r requirements.txt
    ```
3.  **Run the app** to make sure everything is working:
    ```bash
    # macOS
    python3 -m src.macos.main_app
    ```

## 🐛 Reporting Bugs & Feature Requests

If you find a bug or have an idea for a new feature, please check the [Issue Tracker](https://www.google.com/search?q=https://github.com/knowoneactual/Network-Triage-Tool/issues) first to see if it has already been reported.

  * **Bugs:** Open a new issue and describe the error, your OS version, and steps to reproduce it.
  * **Features:** We welcome ideas\! Open a feature request and explain what you want to see and why it would be useful.

## 💻 Development Guidelines

### Code Style

We want to keep the codebase clean and consistent.

  * **Python:** We follow standard Python conventions (PEP 8).
      * **Indentation:** Use **4 spaces** for Python files. (Note: The `.editorconfig` defaults to 2 spaces for other file types, but Python should remain 4).
      * **Linting:** We use `flake8` to check for style issues. Please run it before submitting:
        ```bash
        flake8 . --count --max-complexity=10 --max-line-length=127 --statistics
        ```
  * **Formatting:** This project uses `.editorconfig` and `.prettierrc` to maintain consistent formatting across non-Python files (Markdown, JSON, YAML).

### Testing

We use `pytest` for testing. Please ensure you run the existing tests (and add new ones if applicable) before submitting your changes.

```bash
pytest
```

## 📥 Submitting a Pull Request

1.  **Create a Branch:** Create a new branch for your specific feature or fix.
    ```bash
    git checkout -b feature/amazing-new-feature
    ```
2.  **Commit Changes:** Keep your commit messages clear and descriptive.
3.  **Push to GitHub:** Push your branch to your fork.
4.  **Open a PR:** Go to the original repository and click "New Pull Request."

Please reference any related issues in your Pull Request description (e.g., "Fixes \#12").

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License found in the [LICENSE](https://github.com/KnowOneActual/Network-Triage-Tool/blob/bd79d3d5af2a4ffc125e2f6da0025b8919ffb8e9/LICENSE) file.