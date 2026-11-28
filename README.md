# Typcast

Typcast is a cross-language bridge for generating Typst documents from Python and
the JavaScript/TypeScript ecosystem.

The repository is managed as a Bazel monorepo. The current implementation is an
early foundation: it includes a CSV-backed JSON template generator, the
immutable document model, the semantic validation engine, the validation
against the JSON Schema contract, the fluent builder, and the Typst emitter of
the Python and TypeScript SDKs, and build targets for the two packages.

## Repository layout

- `specs/`: language-independent catalogs and JSON Schema definitions/templates.
- `tools/codegen/`: Python-based template/code generation tooling.
- `tools/schemagen/`: generator that embeds the built schema bundle into a
  source file of an SDK.
- `tools/publish/`: release-time publisher for the schema bundle.
- `bazel/`: reusable Starlark build rules.
- `packages/python/`: Python SDK.
- `packages/typescript/`: TypeScript SDK, also consumable by JavaScript projects
  after compilation.
- `tests/`: cross-package contract and integration tests.

## Requirements

- Bazelisk. The required Bazel version is pinned in `.bazelversion`.
- Git.
- No separately installed Python runtime is required for Bazel targets; the
  Python toolchain is declared in `MODULE.bazel`.

## Build and test

Build all configured targets:

```shell
bazel build //...
```

Run all tests:

```shell
bazel test //...
```

Run the documentation, requirement, decision, and workflow checks:

```shell
bazel test //scripts:docs_checks
```

Run the repository structure, dependency, and toolchain checks:

```shell
bazel run //scripts:repository_checks
```

Build the complete set of currently available JSON Schema artifacts:

```shell
bazel build //specs/schemas:schema_bundle
```

The schema bundle is staged in the Bazel output tree while preserving the
relative paths used by the schemas' `$ref` values:

```text
bazel-bin/
└── specs/
    └── schemas/
        ├── validator.schema.json
        ├── api/
        │   └── types/
        │       ├── alignment.schema.json
        │       ├── length.schema.json
        │       └── paper.schema.json
        └── definitions/
            ├── bound.schema.json
            └── node.schema.json
```

Static schemas are staged with Bazel symlink actions; generated schemas are
produced from the templates and CSV catalogs. Source files remain under
`specs/schemas/`; Bazel does not copy ordinary source files into `bazel-bin`
unless a build action declares an output for them.

Run the generator directly:

```shell
bazel run //tools/codegen:typcast_codegen -- --input "$PWD/specs/schemas/templates/api/types/alignment.schema.json.tmpl" --output "$PWD/out/schemas/alignment.schema.json"
```

Workspace-relative input and output paths fail on Windows. Use absolute paths as
shown, or run the built binary from the repository root.

The generator resolves CSV paths relative to the directory containing the input
template. A placeholder has this form:

```text
<relative/path/to/catalog.csv:ColumnName>
```

All files referenced by a template must also be declared in the corresponding
Bazel generation rule's `catalogs` attribute. This makes the inputs explicit
to Bazel and allows it to invalidate cached outputs when a catalog changes.

## Current schema scope

The bundle implements the document IR of `docs/specifications/document-ir.md`:
the root schema, the margin, the node catalog, and the three generated type
schemas. Every reference in the bundle resolves, and the contract test passes
without a tracked violation.

Two limits remain. The repository does not validate a schema document against
the JSON Schema meta-schema yet, because that needs a JSON Schema
implementation that the project does not depend on. And no release exists, so
the versioned raw URLs are illustrative until the first tag is published.

## Build outputs

Generated and staged files are written to Bazel's output tree. Do not edit
generated artifacts manually. Change the source catalog or template and rebuild
the corresponding target instead.

`MODULE.bazel.lock` is intentionally version-controlled once Bazel generates
it, so dependency resolution remains reproducible across machines.

## Continuous integration

Three GitHub Actions workflows run the repository:

| Workflow | Trigger | Purpose |
|---|---|---|
| Pull request validation | Pull request on `main` | Build, test, clean checkout build, and the documentation gate on Windows and Linux. |
| Main integration | Push to `main` | The same jobs, and the cache for the next run. |
| Release | Tag `v*` | The version check, the tagged build and tests, the published schema bundle, and the versioned raw URLs. |

Every action is pinned to a commit SHA, every workflow has read-only
permissions, and no workflow publishes. See [CI/CD](docs/development/ci-cd.md).

## Schema distribution

Published schemas are served from the repository at the release tag. The
canonical URL of a schema file is:

```text
https://raw.githubusercontent.com/zuudevs/typcast/<VERSION>/specs/schemas/<SCHEMA_FILE>
```

- `<VERSION>` is the Git release tag that publishes the schema, for example
  `v1.0.0`.
- `<SCHEMA_FILE>` is the path of the schema file relative to `specs/schemas/`.

A `main` URL is a development reference only. It is never a stable reference,
and a consumer pins an exact release tag. The repository has no release tag
yet, so every tag URL is illustrative until the first release is tagged.

The covered schema paths and their sources are listed in
[the schema contract](docs/specifications/schema.md). The MVP requires no
dedicated schema domain and no hosting infrastructure.

## Documentation

The product, architecture, contract, and engineering documentation is in
[`docs/`](docs/README.md). Start with the
[documentation index](docs/README.md) and the
[vision and scope](docs/product/vision-and-scope.md).

The documents describe the approved MVP baseline. The SDK exposes the immutable
document model, the JSON serialization, the semantic validation engine, the
fluent builder with its span helpers and its table helpers, and the Typst
emitter. The compiler adapter and the packaging are not implemented yet. The
continuous integration workflows and the release tooling are.

## Contributing

Changes enter through pull requests. Use the pull request template at
`.github/PULL_REQUEST_TEMPLATE.md` and follow the
[contribution and governance rules](docs/governance/contributing.md). The
[contributing guide](CONTRIBUTING.md) lists the checks to run, and the
[code of conduct](CODE_OF_CONDUCT.md) states the expectations for the
community. User-visible changes are recorded in [`CHANGELOG.md`](CHANGELOG.md).

## License

Typcast is licensed under the Apache License 2.0. See [`LICENSE`](LICENSE).

## Security

Report security issues privately as described in [`SECURITY.md`](SECURITY.md).
Do not open a public issue for a suspected vulnerability.
