# Typcast

Typcast is a cross-language bridge for generating Typst documents from Python and
the JavaScript/TypeScript ecosystem.

The repository is managed as a Bazel monorepo. The current implementation is an
early foundation: it includes a CSV-backed JSON template generator and build
targets for the Python and TypeScript packages.

## Repository layout

- \`specs/\`: language-independent catalogs and JSON Schema definitions/templates.
- \`tools/codegen/\`: Python-based template/code generation tooling.
- \`bazel/\`: reusable Starlark build rules.
- \`packages/python/\`: Python SDK.
- \`packages/typescript/\`: TypeScript SDK, also consumable by JavaScript projects
  after compilation.
- \`tests/\`: cross-package contract and integration tests.

## Requirements

- Bazelisk. The required Bazel version is pinned in \`.bazelversion\`.
- Git.
- No separately installed Python runtime is required for Bazel targets; the
  Python toolchain is declared in \`MODULE.bazel\`.

## Build and test

Build all configured targets:

\`\`\`shell
bazel build //...
\`\`\`

Run all tests:

\`\`\`shell
bazel test //...
\`\`\`

Build the generated JSON Schemas:

\`\`\`shell
bazel build //specs/schemas/templates/api/types:generated_schemas
\`\`\`

Run the generator directly:

\`\`\`shell
bazel run //tools/codegen:typcast_codegen -- --input specs/schemas/templates/api/types/alignment.schema.json.tmpl --output out/schemas/alignment.schema.json
\`\`\`

The generator resolves CSV paths relative to the directory containing the input
template. A placeholder has this form:

\`\`\`text
<relative/path/to/catalog.csv:ColumnName>
\`\`\`

All files referenced by a template must also be declared in the corresponding
Bazel generation rule's \`catalogs\` attribute. This makes the inputs explicit
to Bazel and allows it to invalidate cached outputs when a catalog changes.

## Build outputs

Generated files are written to Bazel's output tree. Do not edit generated
artifacts manually. Change the source catalog or template and rebuild the
corresponding target instead.

\`MODULE.bazel.lock\` is intentionally version-controlled once Bazel generates
it, so dependency resolution remains reproducible across machines.
