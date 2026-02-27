# Contributing to Temporal Cortex MCP

Thank you for your interest in contributing to Temporal Cortex MCP Server.

## About This Repo

This is a **documentation and distribution** repository. The MCP server source code is maintained in a separate private repository. The compiled binary is distributed via npm as `@temporal-cortex/cortex-mcp`.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a branch for your changes: `git checkout -b docs/your-change`
4. Make your changes following the guidelines below
5. Push to your fork and submit a pull request

## How to Contribute

### Bug Reports

Found a bug? Search [existing issues](https://github.com/temporal-cortex/mcp/issues) first — it may already be reported. If not, [open a new issue](https://github.com/temporal-cortex/mcp/issues/new?template=bug_report.yml) with:

- Your OS, Node.js version, and MCP client
- Steps to reproduce
- Expected vs actual behavior
- Any error messages or logs

### Feature Requests

Have an idea? [Open an issue](https://github.com/temporal-cortex/mcp/issues/new?template=feature_request.yml) describing your use case and proposed solution.

### Documentation

Improvements to documentation, examples, and guides are welcome via pull requests. This includes:

- Fixing typos or unclear wording
- Adding examples for new MCP clients
- Improving the Google Cloud setup guide
- Translating documentation

### Core Libraries

The open-source computation libraries (Truth Engine, TOON) that power the MCP server live in [temporal-cortex-core](https://github.com/temporal-cortex/core). Code contributions to those libraries are welcome there.

## Commit Messages

Use clear, descriptive commit messages with conventional prefixes:

- `docs: fix broken link in tools.md`
- `docs: add Windsurf setup example`
- `fix: correct OAuth redirect port in setup guide`
- `chore: update CI workflow action versions`

## Pull Request Guidelines

Before submitting a PR, verify:

- [ ] Markdown renders correctly (preview locally or in GitHub)
- [ ] All links are valid and point to the correct targets
- [ ] No sensitive information or credentials included
- [ ] Changes are consistent with existing documentation style
- [ ] CHANGELOG.md updated if this is a user-facing change

See the [pull request template](.github/pull_request_template.md) for the full checklist.

## Code of Conduct

This project follows the [Contributor Covenant v2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

By contributing, you agree that your contributions will be licensed under the MIT license terms of this project.
