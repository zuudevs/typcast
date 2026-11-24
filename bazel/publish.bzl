"""Bazel rules for publishing the Typcast JSON Schema bundle."""

def _relative_path(ctx, path):
    """Returns the path of a bundle file relative to `specs/schemas`."""
    marker = ctx.label.package + "/"
    index = path.path.rfind(marker)
    if index == -1:
        fail("{} is not below the package {}".format(path.path, ctx.label.package))
    return path.path[index + len(marker):]

def _typcast_schema_manifest_impl(ctx):
    manifest = ctx.actions.declare_file(ctx.label.name + ".txt")

    args = ctx.actions.args()
    args.add("manifest")
    args.add("--output", manifest)
    args.add_all([_relative_path(ctx, source) for source in ctx.files.srcs])

    ctx.actions.run(
        executable = ctx.executable._publisher,
        tools = [ctx.attr._publisher[DefaultInfo].files_to_run],
        inputs = ctx.files.srcs,
        outputs = [manifest],
        arguments = [args],
        mnemonic = "TypcastSchemaManifest",
        progress_message = "Writing the schema bundle manifest",
    )

    return [
        DefaultInfo(
            files = depset([manifest]),
        ),
    ]

typcast_schema_manifest = rule(
    implementation = _typcast_schema_manifest_impl,
    attrs = {
        "srcs": attr.label_list(
            allow_files = [".json"],
            mandatory = True,
        ),
        "_publisher": attr.label(
            default = Label("//tools/publish:publish_schemas"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Writes the manifest that names every file of the schema bundle.",
)

def _typcast_schema_archive_impl(ctx):
    archive = ctx.actions.declare_file(ctx.label.name + ".tar.gz")

    # The manifest names the files relative to the package of the manifest
    # rule. The archive rule names every file and its path, because a build
    # output does not live in the source tree.
    args = ctx.actions.args()
    args.add("archive")
    args.add("--output", archive)
    args.add("--prefix", "typcast-schemas")
    for source in ctx.files.srcs:
        args.add(
            "--file",
            "{}={}".format(_relative_path(ctx, source), source.path),
        )

    ctx.actions.run(
        executable = ctx.executable._publisher,
        tools = [ctx.attr._publisher[DefaultInfo].files_to_run],
        inputs = ctx.files.srcs,
        outputs = [archive],
        arguments = [args],
        mnemonic = "TypcastSchemaArchive",
        progress_message = "Writing the schema bundle archive",
    )

    return [
        DefaultInfo(
            files = depset([archive]),
        ),
    ]

typcast_schema_archive = rule(
    implementation = _typcast_schema_archive_impl,
    attrs = {
        "srcs": attr.label_list(
            allow_files = [".json"],
            mandatory = True,
        ),
        "_publisher": attr.label(
            default = Label("//tools/publish:publish_schemas"),
            executable = True,
            cfg = "exec",
        ),
    },
    doc = "Writes the deterministic gzip tarball of the schema bundle.",
)
