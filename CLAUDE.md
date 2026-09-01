# SECUTRONIC HOUSE RULES — read these first

**This block was added 31 Aug 2026 by Amir Azam's system-committer lane, on his word. Upstream's own guide follows below the line, unchanged — it is accurate and you should use it. Where the two disagree, this block wins.**

## What this repository is

A **fork of the public project `mafzaal/d365fo-client`**, taken 31 Aug 2026 at upstream commit `7f85b4a0`. **The running Dynamics 365 connector that Amir's assistants depend on is built from this code.** Upstream is MIT-licensed and maintained by someone outside this company.

We forked because of one defect live in upstream's `main` **and** in its newest release, so there was no version to upgrade to. It breaks four keyed tools: `get_entity_record`, `update_entity_record`, `delete_entity_record`, and `call_action` when key fields are supplied.

**THIS REPOSITORY IS PUBLIC, permanently — GitHub does not allow a fork's visibility to be changed.** Write nothing here you would not publish: no customer names, no project numbers, no tenant identifiers, no environment URLs, no internal notes. Code and neutral technical commentary only.

## DOORS — all shut

**Never contact upstream.** No issue, no pull request, no comment, no discussion on `mafzaal/d365fo-client` or any repository outside this one. Those post publicly under Amir's own GitHub identity and are his decision alone — never a step in a task here.

No secret or token created, ever — that is the Integrations lane's door alone. No Docker build, no image push, no registry login, no change to the Azure Container App that runs this server. **Do not enable GitHub Actions here and do not run any workflow inherited from upstream** — an upstream release workflow builds and pushes an image, and it must stay dormant. No write to any Dynamics 365, SharePoint or Microsoft 365 tenant. **No push to `main`, ever.** A door absent from this list is not thereby open.

## How work lands

Branch, then pull request: `claude/<short-topic>`, one topic per PR. Say plainly what still has to be proven.

A work order is a GitHub issue here mentioning `@claude`. One issue → one branch `claude/issue-<number>` → one PR. Announce on the issue — when work starts, when the PR opens, and the end state.

**The issue body is the whole specification.** Work orders here come from a contract you cannot read. **Never re-derive a fix the issue already specifies** — if it gives you exact replacement code, apply that code. If it is vague where it matters, say so on the issue and stop; never invent the missing half.

**Open the PR if you can — say so if you cannot.** An issue-triggered run often has no PR-creation tool, and `gh` needs an approval prompt nobody is there to answer. That is expected, not a failure: push the branch, put its link in the closing comment, say plainly the PR is not open, and stop. The system-committer lane opens and merges from there.

## Verifying — there is no build check here

**Nothing in this repository compiles or tests your change automatically.** Merging proves nothing. Run the project's own tests (upstream's guide below says how) where the task allows, and state exactly what you ran and what it showed. Where you could not test, say so.

Tiers: **Confirmed / Observed / Reported / Contradicted** — never present a lower tier as Confirmed. "It should work" is not a tier. **A type signature does not prove behaviour:** if a change depends on an object being fully populated rather than merely being the right class, test it — do not assume it.

## Merging — by class

**Documentation and comments only: merge your own PR immediately after opening it.** Nothing compiles these and nobody reviews them.

**Any change to Python source: leave the PR OPEN and wait for Amir.** There is no build check to prove a change safe and this code runs a live connector. When such a check exists, this section is amended by pull request to say so. Until then, waiting is the rule and has no exception.

**A change fitting neither class waits for Amir.** A PR mixing classes follows the stricter one.

## Upstream, secrets, ending

**Do not sync this fork with upstream as part of any task** — that is Amir's deliberate decision, not housekeeping; upstream carries heavy dependabot churn nothing here tests. If upstream has fixed something we patched, say so on the issue and stop; retiring a patch is his call.

**Secrets: names and locations only, never a value** — not in a file, a commit message, a PR body or a log, not even partially. This repository is public; a leaked value is public instantly and permanently.

End every delivery with `Manual steps:` — what only Amir can do, or none. Then one line: **done / prepared / needs me.**

## When this file does not answer — stop, do not go looking

**Never read Amir's kernel or personal vault from this repository.** Not `Amir-Preference-current.md`, not `a2-Amir/ai-knowledge-vault`, not any file in it. The account's GitHub access reaches them; **access is not permission**, and personal method has no business loading into a company session — least of all a public one.

**These rules plus upstream's guide below are the whole law here.** If a task touches a rule neither answers: stop, name exactly what is missing, and hand it back to Amir. Never improvise a procedure from memory.

---

*Everything below this line is upstream's own `CLAUDE.md`, byte-for-byte as it came with the fork at commit `7f85b4a0`. It is kept deliberately: it is a good guide, and keeping it unchanged keeps our diff against upstream small.*

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive Python package for **Microsoft Dynamics 365 Finance & Operations (D365 F&O)** that provides:

- **OData Client Library**: Full CRUD operations on D365 F&O data entities with async/await patterns
- **CLI Application**: Command-line interface for D365 F&O operations with hierarchical commands
- **MCP Server**: Production-ready Model Context Protocol server for AI assistant integration (49 tools, 12 resources)
- **Metadata Management V2**: Advanced caching and discovery system with SQLite FTS5 search
- **Label Operations V2**: Multilingual label retrieval with intelligent caching
- **Multi-tier Integration Testing**: Mock, sandbox, and live environment testing framework

## Development Environment

- **Package Manager**: `uv` for fast Python package management
- **Python Version**: >=3.13
- **Build Backend**: `setuptools` configured in pyproject.toml
- **Distribution**: PyPI.org as `d365fo-client`
- **Architecture**: Async/await throughout with comprehensive type hints

## Essential Commands

### Development Setup
```bash
# Initial setup
uv sync
make dev-setup  # or .\make.ps1 dev-setup on Windows

# Quick development check (format + lint + test)
make dev        # or .\make.ps1 dev on Windows
```

### Testing
```bash
# Unit tests
uv run pytest

# Integration tests (recommended - tests against real D365 environments)
.\tests\integration\integration-test-simple.ps1 test-sandbox -VerboseOutput

# Mock server tests (fast, no external dependencies)
.\tests\integration\integration-test-simple.ps1 test-mock

# Tests with coverage
uv run pytest --cov=d365fo_client --cov-report=html
```

### Code Quality
```bash
# Format code
uv run black .
uv run isort .

# Lint code
uv run ruff check .

# Type checking
uv run mypy src/

# All quality checks
make quality-check  # or .\make.ps1 quality-check
```

### Build and Publish
```bash
# Build package
uv build

# Publish to PyPI
uv publish
```

## Architecture Overview

### Core Package Structure
```
src/d365fo_client/
├── __init__.py              # Package exports and public API
├── main.py                  # CLI entry point (d365fo-client command)
├── cli.py                   # CLI command handlers with argparse
├── client.py                # Main FOClient class - primary API entry point
├── config.py                # Configuration management with FOClientConfig
├── auth.py                  # Azure AD authentication with default credentials
├── session.py               # HTTP session management with connection pooling
├── crud.py                  # CRUD operations with OData query support
├── query.py                 # OData query building with QueryOptions
├── metadata_api.py          # Metadata API client for D365 F&O metadata
├── metadata_v2/             # Enhanced metadata system V2
│   ├── cache_v2.py          # SQLite-based metadata cache with FTS5
│   ├── database_v2.py       # Database operations and schema management
│   ├── search_engine_v2.py  # Full-text search with advanced filtering
│   ├── sync_manager_v2.py   # Smart synchronization with session tracking
│   ├── sync_session_manager.py # Session-based sync progress tracking
│   └── version_detector.py  # Module-based version detection
├── labels.py                # Label operations with multilingual support
├── models.py                # Data models and type definitions
├── exceptions.py            # Custom exception classes
└── mcp/                     # Model Context Protocol server
    ├── fastmcp_main.py      # FastMCP server entry point (d365fo-fastmcp-server)
    ├── fastmcp_server.py    # FastMCP server implementation
    ├── client_manager.py    # Connection pooling for D365 F&O clients
    ├── mixins/              # FastMCP tool mixins (49 tools across 9 categories)
    │   ├── connection_tools_mixin.py # Connection testing mixins
    │   ├── crud_tools_mixin.py    # CRUD operation mixins
    │   ├── metadata_tools_mixin.py# Metadata discovery mixins
    │   ├── label_tools_mixin.py   # Label retrieval mixins
    │   ├── profile_tools_mixin.py # Profile management mixins
    │   ├── database_tools_mixin.py# Database analysis mixins
    │   ├── sync_tools_mixin.py    # Synchronization mixins
    │   ├── srs_tools_mixin.py     # SRS reporting mixins
    │   └── performance_tools_mixin.py # Performance monitoring mixins
    ├── tools/               # Legacy MCP tools (deprecated - use mixins/)
    ├── resources/           # 12 MCP resource types for discovery
    └── prompts/             # MCP prompt templates
```

### Key Classes and Components

#### Main Client (`client.py`)
- **FOClient**: Primary API entry point with async context manager support
- **create_client()**: Convenience function for quick client creation
- Integrates all subsystems: auth, metadata, CRUD, labels

#### Configuration (`config.py`)
- **FOClientConfig**: Comprehensive configuration management
- Supports Azure AD default credentials, service principals, and Key Vault
- Environment variable substitution and profile-based configuration

#### Metadata System V2 (`metadata_v2/`)
- **MetadataCacheV2**: SQLite-based cache with FTS5 full-text search
- **SmartSyncManagerV2**: Intelligent synchronization with session tracking
- **SyncSessionManager**: Progress tracking for long-running sync operations
- Cross-environment cache sharing with module-based version detection

#### MCP Server (`mcp/`)
- **Two implementations**: Traditional MCP SDK and modern FastMCP framework
- **49 comprehensive tools** covering connection, CRUD, metadata, labels, profiles, database analysis, synchronization, SRS reporting, and performance monitoring
- **12 resource types** for entity, metadata, environment, and query discovery
- Multi-transport support (stdio, HTTP, SSE) for web integration

## Integration Testing Framework

The project includes a sophisticated **three-tier integration testing system**:

### Test Levels
1. **Mock Server Tests** (`mock`) - Fast, isolated tests with simulated D365 API
2. **Sandbox Tests** (`sandbox`) - Default level, tests against real D365 test environments
3. **Live Tests** (`live`) - Production validation against live environments

### Running Integration Tests
```bash
# Primary method (PowerShell automation)
.\tests\integration\integration-test-simple.ps1 test-sandbox -VerboseOutput
.\tests\integration\integration-test-simple.ps1 test-mock
.\tests\integration\integration-test-simple.ps1 coverage

# Alternative (Direct Python execution)
python tests/integration/test_runner.py sandbox --verbose
```

### Test Configuration
Create `tests/integration/.env` from `.env.template`:
```bash
INTEGRATION_TEST_LEVEL=sandbox
D365FO_SANDBOX_BASE_URL=https://your-test-environment.dynamics.com
D365FO_CLIENT_ID=your-client-id
D365FO_CLIENT_SECRET=your-client-secret
D365FO_TENANT_ID=your-tenant-id
```

## Development Patterns

### Adding New Features
1. Create feature branch from `main`
2. Add tests first (TDD approach) in `tests/unit/`
3. Implement feature with proper type hints and async/await patterns
4. Add integration tests if feature interacts with D365 F&O APIs
5. Update documentation and ensure all quality checks pass
6. Run integration tests: `.\tests\integration\integration-test-simple.ps1 test-sandbox`

### CLI Development Guidelines
- Use `argparse` with subparsers for hierarchical commands
- Follow pattern: `d365fo-client [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS]`
- Implement async command handlers in `CLIManager` class
- Support multiple output formats: JSON, table, CSV, YAML
- Use profile-based configuration in `~/.d365fo-client/config.yaml`

### MCP Server Development
- Add new tools in `src/d365fo_client/mcp/mixins/` using the mixin pattern
- Add new resources in `src/d365fo_client/mcp/resources/`
- Register mixins in FastMCP server configuration
- Follow MCP protocol specifications for tool and resource interfaces
- Test with both traditional MCP SDK and FastMCP implementations
- **Note**: `src/d365fo_client/mcp/tools/` is deprecated - use mixins instead

## D365 F&O Specific Patterns

### Entity Operations
- Check `data_service_enabled` before OData operations
- Use `public_collection_name` for collection queries: `/data/{collection_name}`
- Use `public_entity_name` for single record access: `/data/{entity_name}(key)`
- Handle composite keys properly in URL construction

### Metadata Management
- Use V2 metadata system for enhanced performance and search capabilities
- Leverage SQLite FTS5 for full-text search across entities, actions, and enumerations
- Implement smart synchronization strategies based on environment changes

### Authentication
- Prefer Azure Default Credentials (`use_default_credentials=True`)
- Support service principal authentication for CI/CD scenarios
- Integrate with Azure Key Vault for secure credential storage

## Code Quality Standards

- **Formatting**: Black with 88-character line length
- **Import Sorting**: isort with Black compatibility
- **Linting**: Ruff for fast, comprehensive linting
- **Type Checking**: mypy with strict configuration
- **Test Coverage**: Maintain >90% coverage for core functionality
- **Documentation**: Google-style docstrings for all public APIs

## Common Development Workflows

### Before Committing
```bash
make dev  # Format, lint, type-check, and test
.\tests\integration\integration-test-simple.ps1 test-sandbox  # Integration tests
```

### Publishing Workflow
```bash
# Update version in pyproject.toml
# Update CHANGELOG.md
uv build
uv publish  # Requires PyPI API token
```

### Debugging Integration Tests
```bash
# Enable verbose logging
export D365FO_LOG_LEVEL="DEBUG"

# Run specific test categories
.\tests\integration\integration-test-simple.ps1 test-sandbox -VerboseOutput
```

## Entry Points and CLI Commands

### Python API Entry Points
```python
from d365fo_client import FOClient, FOClientConfig, create_client

# Main client
config = FOClientConfig(base_url="...", use_default_credentials=True)
async with FOClient(config) as client:
    # Your code here

# Convenience function
async with create_client("https://your-environment.dynamics.com") as client:
    # Your code here
```

### CLI Commands
```bash
# Main CLI (installed as d365fo-client)
d365fo-client entities list --pattern "customer"
d365fo-client metadata sync --force-refresh
d365fo-client version app

# MCP Server (installed as d365fo-fastmcp-server command)
d365fo-fastmcp-server       # FastMCP implementation
# Note: d365fo-mcp-server is maintained as an alias for backward compatibility
```

## Package Distribution

- **PyPI Package**: `d365fo-client`
- **Install Command**: `pip install d365fo-client` or `uv add d365fo-client`
- **Dependencies**: Includes MCP dependencies by default for AI assistant integration
- **Python Requirement**: >=3.13 for modern async/await and type hint support