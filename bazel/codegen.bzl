"""Bazel rules for generating Typcast JSON artifacts."""

def _typcast_json_schema_impl(ctx):
    output_name = ctx.attr.output

    if "/" in output_name or "\\" in output_name:
        fail("'output' must be a file name, not a path: {}".format(output_name))

    output = ctx.actions.declare_file(output_name)

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
        progress_message = "Generating JSON artifact %{output}",
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
    doc = "Expands a JSON template using its declared CSV catalog inputs.",
)
