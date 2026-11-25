# Contributing to Typcast

Typcast generates Typst documents from Python and TypeScript. The repository
is a Bazel monorepo, and the project is at an early stage: the schema contract,
the documentation, and the build tooling are in place, while the SDK core is
not implemented yet.

Thank you for your interest. This guide describes how to propose a change.

## Before you start

| Question | Answer |
|---|---|
| Where is the scope defined? | [Vision and scope](docs/product/vision-and-scope.md) |
| Where are the requirements? | [Requirements traceability](docs/requirements/traceability.md) |
| Where are the decisions? | [Architecture decision records](docs/decisions/README.md) |
| What is the current state? | [Documentation index](docs/README.md) |
| What may I contribute under? | [Apache-2.0 license](LICENSE) |
| What is expected of me? | [Code of conduct](CODE_OF_CONDUCT.md) |
| How do I report a security issue? | [Security policy](SECURITY.md) |

Issues are free-form reports. The project uses a single pull request template
and no issue templates.

## Development setup

- Install [Bazelisk](https://github.com/bazelbuild/bazelisk). The Bazel version
  is pinned in `.bazelversion`, and Bazelisk reads it.
- Clone the repository and build it:

  ```shell
  bazel build //...
  ```

- Python 3.11 or newer runs the tools locally. The Bazel toolchain is hermetic
  and pinned by `MODULE.bazel.lock`.
- Node.js 22 or newer is needed only for the TypeScript package, and Bazel
  fetches the compiler version from the root `package.json`. There is no
  install step for the workspace.
- The Typst CLI is optional. It is needed only for the compiler integration
  tests, which are not implemented yet.

## Working on a change

1. Branch from `main` with a short-lived branch name, for example
   `docs/schema-distribution` or `fix/page-margin`.
2. Make the change, and keep it within the scope of the issue or of the gap it
   closes.
3. Update the documents that the change affects.
4. Run the checks below.
5. Open a pull request against `main` and fill in the template.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/):
`feat:`, `fix:`, `refactor(specs):`, `chore(bazel):`, `build:`, `test:`. Use a
scope when it clarifies the area.

## Checks to run

```shell
bazel build //...
bazel test //...
git diff --check
```

`bazel test //...` runs the generator tests, the publisher tests, the
documentation checks, and the schema bundle checks. The individual targets are
listed in [Build](docs/development/build.md).

The documentation checks cover the encoding, the Markdown structure, the
internal links, the requirement index, the decision index, and the schema
references. They are the same checks that the CI lane will run.

## Requirements and decisions

- A change to a requirement updates the requirement in its source document and
  `docs/requirements/traceability.md` in the same change. Requirement IDs are
  never reused or renumbered.
- A significant decision needs an architecture decision record. Add the record
  under `docs/decisions/`, and update the index in `docs/decisions/README.md`.
- A change to the schema contract updates the templates or the catalogs, and
  the bundle validation must pass:

  ```shell
  bazel test //specs/schemas:schema_tests
  ```

- Generated schemas are never committed to the development branch. The
  published bundle in a tagged release commit is the only exception.

## Documentation

- The documentation index is `docs/README.md`. Every document has exactly one
  level-1 heading, declares the language of every code fence, and uses UTF-8
  without a byte order mark and LF line endings.
- Add a new document to the `docs_sources` group in the root `BUILD.bazel`, so
  that the documentation checks cover it.
- The style rules are in [Documentation](docs/development/documentation.md).

## Pull requests

The pull request template is `.github/PULL_REQUEST_TEMPLATE.md`. Fill in every
section that applies. A section or a checkbox that does not apply is removed
or marked "Not applicable". The template records the commands that were run and
their results, so a reviewer can repeat them.

A pull request needs at least one maintainer approval. Direct pushes to `main`
are not accepted. Required checks must pass before the merge.

## Changelog

User-visible changes are recorded in `CHANGELOG.md` under `Unreleased`. A
breaking change is marked in the commit and in the changelog.

## Security

Do not open a public issue for a suspected vulnerability. Follow the
[security policy](SECURITY.md) and report privately.

## License

Contributions are accepted under the [Apache-2.0 license](LICENSE). By
contributing, you agree that your contribution is licensed under it.
