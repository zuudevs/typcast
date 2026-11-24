"""Bazel rules for assembling Typcast JSON Schema artifacts."""

def _declare_schema_output(ctx, output_path):
    if not output_path:
        fail("'output' must not be empty.")

    if output_path.startswith("/") or "\\" in output_path:
        fail("'output' must be a relative path using '/': {}".format(output_path))

    for segment in output_path.split("/"):
        if segment in ["", ".", ".."]:
            fail("'output' contains an invalid path segment: {}".format(output_path))

    return ctx.actions.declare_file(output_path)

def _typcast_json_schema_impl(ctx):
    output = _declare_schema_output(ctx, ctx.attr.output)

    args = ctx.actions.args()
    args.add("--input", ctx.file.template.path)
    args.add("--output", output.path)

    ctx.actions.run(
        executable = ctx.executable._generator,
        tools = [ctx.attr._generator[DefaultInfo].files_to_run],
        inputs = depset(
            direct = [ctx.file.template] + ctx.files.catalogs,
        ),
        outputs = [output],
        arguments = [args],
        mnemonic = "TypcastJsonSchema",
        progress_message = "Generating JSON Schema %{output}",
    )

    return [
        DefaultInfo(
            files = depset([output]),
        ),
    ]

typcast_json_schema = rule(
    implementation = _typcast_json_schema_impl,
    attrs = {
        "template": attr.label(
            allow_single_file = [".tmpl"],
            mandatory = True,
        ),
        "catalogs": attr.label_list(
            allow_files = [".csv"],
        ),
        "output": attr.string(
            mandatory = True,
        ),
        "_generator": attr.label(
            default = Label("//tools/codegen:typcast_codegen"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Expands a JSON template and writes the generated schema at the requested package-relative path.",
)

def _typcast_schema_copy_impl(ctx):
    output = _declare_schema_output(ctx, ctx.attr.output)

    ctx.actions.symlink(
        output = output,
        target_file = ctx.file.source,
        progress_message = "Staging JSON Schema %{output}",
    )

    return [
        DefaultInfo(
            files = depset([output]),
        ),
    ]

typcast_schema_copy = rule(
    implementation = _typcast_schema_copy_impl,
    attrs = {
        "source": attr.label(
            allow_single_file = [".json"],
            mandatory = True,
        ),
        "output": attr.string(
            mandatory = True,
        ),
    },
    doc = "Stages an existing JSON Schema source file into the Bazel output tree.",
)
