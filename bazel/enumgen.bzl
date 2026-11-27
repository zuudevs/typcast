"""Bazel rules for expanding a CSV catalog into a source file of an SDK."""

def _typcast_enum_source_impl(ctx):
    output = ctx.actions.declare_file(ctx.attr.output)

    args = ctx.actions.args()
    args.add("--catalog", ctx.file.catalog.path)
    args.add("--column", ctx.attr.column)
    args.add("--name", ctx.attr.constant)
    args.add("--language", ctx.attr.language)
    args.add("--label", ctx.attr.label)
    args.add("--output", output.path)

    ctx.actions.run(
        executable = ctx.executable._generator,
        tools = [ctx.attr._generator[DefaultInfo].files_to_run],
        inputs = depset(direct = [ctx.file.catalog]),
        outputs = [output],
        arguments = [args],
        mnemonic = "TypcastEnumSource",
        progress_message = "Generating enum source %{output}",
    )

    return [
        DefaultInfo(
            files = depset([output]),
        ),
    ]

typcast_enum_source = rule(
    implementation = _typcast_enum_source_impl,
    attrs = {
        "catalog": attr.label(
            allow_single_file = [".csv"],
            mandatory = True,
        ),
        "column": attr.string(
            mandatory = True,
        ),
        "constant": attr.string(
            mandatory = True,
        ),
        "language": attr.string(
            mandatory = True,
        ),
        "label": attr.string(
            mandatory = True,
        ),
        "output": attr.string(
            mandatory = True,
        ),
        "_generator": attr.label(
            default = Label("//tools/enumgen:typcast_enumgen"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Expands a column of a CSV catalog into a source file of an SDK. The catalog is the only input of the rule, so the values of the catalog reach the SDK without a hand-written copy that could drift.",
)
