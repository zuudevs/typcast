"""Bazel rules for embedding the Typcast JSON Schema contract into an SDK.

The SDKs carry the schema contract in a generated source file, so that a
published package needs no file of the repository at run time. The rule reads
the schema bundle that `//specs/schemas:schema_bundle` produces and writes
one source file per SDK.
"""

def _declare_output(ctx, output_path):
    if not output_path:
        fail("'output' must not be empty.")

    if output_path.startswith("/") or "\\" in output_path:
        fail("'output' must be a relative path using '/': {}".format(output_path))

    for segment in output_path.split("/"):
        if segment in ["", ".", ".."]:
            fail("'output' contains an invalid path segment: {}".format(output_path))

    return ctx.actions.declare_file(output_path)

def _relative_path(root, path):
    """Returns the path of a bundle file relative to the root of the bundle."""
    if not root:
        fail("'root' must not be empty.")

    prefix = root + "/"
    if not path.startswith(prefix):
        fail("{} is not below the root {}".format(path, root))

    return path[len(prefix):]

def _typcast_schema_source_impl(ctx):
    output = _declare_output(ctx, ctx.attr.output)

    args = ctx.actions.args()
    args.add("--language", ctx.attr.language)
    args.add("--output", output.path)
    for source in ctx.files.srcs:
        args.add(
            "--file",
            "{}={}".format(
                _relative_path(ctx.attr.root, source.short_path),
                source.path,
            ),
        )

    ctx.actions.run(
        executable = ctx.executable._generator,
        tools = [ctx.attr._generator[DefaultInfo].files_to_run],
        inputs = ctx.files.srcs,
        outputs = [output],
        arguments = [args],
        mnemonic = "TypcastSchemaSource",
        progress_message = "Embedding the JSON Schema contract %{output}",
    )

    return [
        DefaultInfo(
            files = depset([output]),
        ),
    ]

typcast_schema_source = rule(
    implementation = _typcast_schema_source_impl,
    attrs = {
        "srcs": attr.label_list(
            allow_files = [".json"],
            mandatory = True,
        ),
        "root": attr.string(
            mandatory = True,
            doc = "The path of the bundle relative to the root of the workspace.",
        ),
        "language": attr.string(
            mandatory = True,
            values = ["python", "typescript"],
        ),
        "output": attr.string(
            mandatory = True,
        ),
        "_generator": attr.label(
            default = Label("//tools/schemagen:typcast_schemagen"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Writes a source file of an SDK that holds the schema documents of the bundle. The references of the bundle are relative to the document that holds them, so the rule keeps the path of every file relative to the root of the bundle.",
)
