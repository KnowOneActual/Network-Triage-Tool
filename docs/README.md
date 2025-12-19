# Documentation Index

Central hub for all Network Triage Tool documentation.

## Quick Links

- **[README](README.md)** - Project overview and features
- **[Installation Guide](INSTALLATION-GUIDE.md)** - Setup instructions for all platforms
- **[Phase 3 Quick Start](PHASE3-QUICK-START.md)** - Get started in 5 minutes
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project
- **[Changelog](CHANGELOG.md)** - Version history and updates

## Getting Started

### New Users

Start here if you're new to the Network Triage Tool:

1. **[README.md](README.md)** - Understand what the tool does and its key features
2. **[INSTALLATION-GUIDE.md](INSTALLATION-GUIDE.md)** - Install on your platform (Windows, macOS, Linux)
3. **[PHASE3-QUICK-START.md](PHASE3-QUICK-START.md)** - Run your first diagnostics in under 5 minutes
4. **[docs/PHASE3_DIAGNOSTICS.md](docs/PHASE3_DIAGNOSTICS.md)** - Explore the full API reference

### Existing Users

Upgrading or looking for specific information:

1. **[RELEASE-NOTES-PHASE3.md](RELEASE-NOTES-PHASE3.md)** - What's new in v0.3.0
2. **[CHANGELOG.md](CHANGELOG.md)** - Detailed version history
3. **[ROADMAP.md](ROADMAP.md)** - Upcoming features and development plans
4. **[PHASE4-INTEGRATION-ROADMAP.md](PHASE4-INTEGRATION-ROADMAP.md)** - Next phase: TUI integration

### Contributors & Developers

Contributing to the project:

1. **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines and workflow
2. **[ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md)** - Error handling patterns and best practices
3. **[tests/README.md](tests/)** - Testing infrastructure and running tests
4. **[.github/workflows/](.github/workflows/)** - CI/CD pipeline configuration

## Documentation by Category

### Installation & Setup

| Document | Description | Audience |
|----------|-------------|----------|
| [INSTALLATION-GUIDE.md](INSTALLATION-GUIDE.md) | Complete setup instructions for Windows, macOS, and Linux | All users |
| [README.md](README.md) | Quick installation via `pip install -e .` | All users |
| [PHASE3-QUICK-START.md](PHASE3-QUICK-START.md) | Prerequisites and verification steps | New users |

### User Guides

| Document | Description | Audience |
|----------|-------------|----------|
| [PHASE3-QUICK-START.md](PHASE3-QUICK-START.md) | Practical examples for DNS, port, and latency utilities | All users |
| [docs/PHASE3_DIAGNOSTICS.md](docs/PHASE3_DIAGNOSTICS.md) | Complete API reference with detailed function signatures | Advanced users |
| [README.md](README.md) | Feature overview and keyboard shortcuts | All users |

### API Reference

| Document | Description | Modules Covered |
|----------|-------------|-----------------|
| [docs/PHASE3_DIAGNOSTICS.md](docs/PHASE3_DIAGNOSTICS.md) | Comprehensive API documentation (18KB+) | dns_utils, port_utils, latency_utils |
| [PHASE3-QUICK-START.md](PHASE3-QUICK-START.md) | Quick reference with code examples | All Phase 3 modules |
| Source code docstrings | Inline documentation | All modules |

### Release Information

| Document | Description | Version |
|----------|-------------|----------|
| [RELEASE-NOTES-PHASE3.md](RELEASE-NOTES-PHASE3.md) | Phase 3 release notes with features, testing, and metrics | v0.3.0 |
| [CHANGELOG.md](CHANGELOG.md) | Complete version history from v0.1.0 to present | All versions |
| [GitHub Releases](https://github.com/knowoneactual/Network-Triage-Tool/releases) | Official release artifacts and downloads | All versions |

### Development & Planning

| Document | Description | Status |
|----------|-------------|--------|
| [ROADMAP.md](ROADMAP.md) | High-level project roadmap and milestones | Active |
| [PHASE4-INTEGRATION-ROADMAP.md](PHASE4-INTEGRATION-ROADMAP.md) | Detailed Phase 4 planning (TUI integration) | Planning |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Development workflow and coding standards | Active |
| [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) | Patterns for robust error handling | Active |

### Testing & Quality

| Document | Description | Coverage |
|----------|-------------|-----------|
| [tests/test_phase3_diagnostics.py](tests/test_phase3_diagnostics.py) | Phase 3 unit tests (22 tests, 100% passing) | Phase 3 modules |
| [RELEASE-NOTES-PHASE3.md](RELEASE-NOTES-PHASE3.md) | Testing metrics and CI/CD information | v0.3.0 |
| [.github/workflows/phase3-tests.yml](.github/workflows/phase3-tests.yml) | Automated testing configuration | All platforms |

### Project Management

| Document | Description | Purpose |
|----------|-------------|----------|
| [LICENSE](LICENSE) | MIT License terms | Legal |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Code of conduct and PR process | Contributors |
| [.editorconfig](.editorconfig) | Editor configuration for consistent formatting | Developers |
| [.prettierrc](.prettierrc) | Code formatting rules | Developers |

## Documentation by Phase

### Phase 1: Error Handling Foundation
- [CHANGELOG.md](CHANGELOG.md) - v0.11.0 release notes
- [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) - Error handling patterns introduced

### Phase 2: TUI Framework
- [README.md](README.md) - TUI features and keyboard shortcuts
- [CHANGELOG.md](CHANGELOG.md) - v0.2.x releases

### Phase 3: Advanced Diagnostics (Current)
- **[PHASE3-QUICK-START.md](PHASE3-QUICK-START.md)** - Quick start guide
- **[docs/PHASE3_DIAGNOSTICS.md](docs/PHASE3_DIAGNOSTICS.md)** - Complete API reference
- **[RELEASE-NOTES-PHASE3.md](RELEASE-NOTES-PHASE3.md)** - Release notes and metrics
- **[tests/test_phase3_diagnostics.py](tests/test_phase3_diagnostics.py)** - Test suite
- **[CHANGELOG.md](CHANGELOG.md)** - v0.3.0 changelog

### Phase 4: TUI Integration (Planned)
- **[PHASE4-INTEGRATION-ROADMAP.md](PHASE4-INTEGRATION-ROADMAP.md)** - Detailed planning and timeline
- **[ROADMAP.md](ROADMAP.md)** - High-level Phase 4 overview

## Quick Reference

### Common Tasks

**Installing the tool:**
```bash
# See: INSTALLATION-GUIDE.md
git clone https://github.com/knowoneactual/Network-Triage-Tool.git
cd Network-Triage-Tool
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

**Running the TUI:**
```bash
# See: README.md
network-triage
```

**Using Phase 3 utilities:**
```python
# See: PHASE3-QUICK-START.md
from src.shared.dns_utils import resolve_hostname
result = resolve_hostname('example.com')
print(result.ipv4_addresses)
```

**Running tests:**
```bash
# See: CONTRIBUTING.md
pytest tests/test_phase3_diagnostics.py -v
```

**Contributing code:**
```bash
# See: CONTRIBUTING.md
git checkout -b feature/my-feature
# Make changes
pytest tests/ -v
git commit -m "feat: Add new feature"
git push origin feature/my-feature
# Open PR on GitHub
```

### Troubleshooting

**Installation issues:**
- See [INSTALLATION-GUIDE.md](INSTALLATION-GUIDE.md) - Troubleshooting section

**Test failures:**
- See [CONTRIBUTING.md](CONTRIBUTING.md) - Running tests section
- Check [RELEASE-NOTES-PHASE3.md](RELEASE-NOTES-PHASE3.md) - Known issues

**Error handling:**
- See [ERROR_HANDLING_GUIDE.md](ERROR_HANDLING_GUIDE.md) - Common patterns

**Platform-specific problems:**
- See [INSTALLATION-GUIDE.md](INSTALLATION-GUIDE.md) - Platform-specific setup
- See [RELEASE-NOTES-PHASE3.md](RELEASE-NOTES-PHASE3.md) - Known platform limitations

## External Resources

### GitHub
- **Repository:** https://github.com/knowoneactual/Network-Triage-Tool
- **Issues:** https://github.com/knowoneactual/Network-Triage-Tool/issues
- **Discussions:** https://github.com/knowoneactual/Network-Triage-Tool/discussions
- **Releases:** https://github.com/knowoneactual/Network-Triage-Tool/releases
- **CI/CD:** https://github.com/knowoneactual/Network-Triage-Tool/actions

### Dependencies
- **Textual Framework:** https://textual.textualize.io/
- **Python Documentation:** https://docs.python.org/3/
- **Scapy:** https://scapy.net/
- **Nmap:** https://nmap.org/

## Documentation Standards

### Writing Guidelines

All documentation in this project follows these principles:

1. **Clarity:** Write for users of all skill levels
2. **Completeness:** Include all necessary information
3. **Conciseness:** Avoid unnecessary verbosity
4. **Code Examples:** Provide working, tested examples
5. **Cross-references:** Link to related documentation
6. **Maintenance:** Keep documentation current with code changes

### Formatting Conventions

- **Markdown:** All documentation uses Markdown format
- **Code blocks:** Include language specifiers (```python, ```bash)
- **Headers:** Use ATX-style headers (# ## ###)
- **Links:** Use reference-style links for readability
- **Tables:** Use for structured comparisons
- **Emojis:** Use sparingly for visual emphasis (✅ ❌ 🚀)

### Documentation Updates

When contributing code changes:

1. Update relevant documentation files
2. Add examples to PHASE3-QUICK-START.md if introducing new features
3. Update API reference in docs/PHASE3_DIAGNOSTICS.md
4. Add entry to CHANGELOG.md
5. Update README.md if user-facing features change

See [CONTRIBUTING.md](CONTRIBUTING.md) for the complete contribution workflow.

## Documentation Metrics

**Total Documentation:**
- 14+ documentation files
- ~150KB total content
- 30+ code examples
- 100% API coverage

**By Type:**
- User guides: 4 files
- API reference: 1 file (18KB)
- Development guides: 3 files
- Project management: 6 files

**Maintenance:**
- Last updated: December 2025 (Phase 3)
- Update frequency: Every release
- Review cycle: Quarterly

## Getting Help

### Community Support

1. **Check documentation first** - Use this index to find relevant docs
2. **Search existing issues** - https://github.com/knowoneactual/Network-Triage-Tool/issues
3. **Ask in discussions** - https://github.com/knowoneactual/Network-Triage-Tool/discussions
4. **Open a new issue** - For bugs or feature requests

### Reporting Documentation Issues

Found a problem with the documentation?

1. Open an issue with the label `documentation`
2. Specify which document needs updating
3. Describe the problem or suggest improvements
4. Submit a PR if you can fix it yourself

## Documentation Roadmap

### Planned Additions

**Phase 4 (Q1 2026):**
- TUI widget documentation
- Video tutorials and walkthroughs
- Interactive examples
- User guide with screenshots

**Phase 5+ (Future):**
- API versioning documentation
- Plugin development guide
- Architecture deep-dive
- Performance optimization guide

### Continuous Improvements

- Expand troubleshooting sections
- Add more code examples
- Create FAQ document
- Improve cross-references
- Add diagrams and flowcharts

## Contributing to Documentation

Documentation contributions are highly valued!

**Easy contributions:**
- Fix typos and formatting
- Add missing examples
- Improve clarity of existing docs
- Add troubleshooting tips

**Medium contributions:**
- Write new sections
- Create tutorials
- Improve API documentation
- Add diagrams

**Advanced contributions:**
- Create video walkthroughs
- Design documentation structure
- Write comprehensive guides
- Maintain documentation index

See [CONTRIBUTING.md](CONTRIBUTING.md) for the contribution process.

---

## Quick Navigation

**By Role:**
- [New User](#new-users) | [Existing User](#existing-users) | [Contributor](#contributors--developers)

**By Category:**
- [Installation](#installation--setup) | [User Guides](#user-guides) | [API Reference](#api-reference) | [Development](#development--planning)

**By Phase:**
- [Phase 1](#phase-1-error-handling-foundation) | [Phase 2](#phase-2-tui-framework) | [Phase 3](#phase-3-advanced-diagnostics-current) | [Phase 4](#phase-4-tui-integration-planned)

---

**Last Updated:** December 19, 2025 (v0.3.0)  
**Maintained By:** Network Triage Tool Contributors  
**Questions?** Open a [discussion](https://github.com/knowoneactual/Network-Triage-Tool/discussions) on GitHub
