# Security policy

## Reporting a vulnerability

Please report security issues privately. Do not open a public issue, a pull
request, or a discussion for a suspected vulnerability.

The preferred channel is GitHub private vulnerability reporting:

1. Open the repository's **Security** tab.
2. Select **Report a vulnerability**.
3. Submit the report through the private advisory form.

Private vulnerability reporting must be enabled by the repository owner. If the
button is unavailable, use the **Advisories -> Report a vulnerability** link on
the repository's security page, or contact the maintainer through the
repository owner profile if no private channel is configured yet.

Every report is handled under the response targets in this document.

### What to include

- The affected version of Typcast and of the Typst CLI.
- The platform and runtime: Windows or Linux, Python version, Node.js version.
- A minimal reproduction, ideally a document IR fixture or a short script.
- The diagnostic code, such as `TYPCAST-COMPILER-0004`, and the raw compiler
  output if it is relevant.
- The impact you observed, including whether a path escape, arbitrary file
  read, command execution, or information disclosure was possible.

Remove secrets, credentials, and private document content from the report.
Reports are handled under the terms in [Contributing and governance](docs/governance/contributing.md).

## Supported versions

| Version | Supported |
|---|---|
| `1.x.y` | Yes |
| `0.x.y` | No |
| `main` | Best effort, not a release |

Security fixes are released for the latest stable `1.x.y` release. A fix is
backported to the previous `1.x` patch line only when the maintainer judges the
risk to be significant and the backport is low risk.

## Response targets

| Stage | Target |
|---|---|
| Acknowledgement of a valid report | 3 business days |
| Initial triage and impact assessment | 7 business days |
| Fix or mitigation plan for critical and high severity issues | 14 calendar days |
| Fix release for critical and high severity issues | 30 calendar days |
| Fix release for medium and low severity issues | Next scheduled release |
| Coordinated disclosure window after a fix ships | 90 days |

Severity is assessed with CVSS 3.1 as a starting point. A report that is not a
vulnerability, such as a compiler crash caused by invalid raw Typst, is
answered as "not affected" with a short explanation and is still tracked
privately until the reporter agrees with the classification.

## Disclosure process

1. The maintainer confirms the report privately and assigns an identifier.
2. Triage establishes affected versions, severity, and whether the report is
   accepted.
3. A fix is prepared in a private branch, reviewed, and tested.
4. The fix is released with a security note in `CHANGELOG.md`.
5. A GitHub Security Advisory is published. The reporter is credited unless
   they ask not to be.
6. The advisory is made public after the release is available, or after the
   coordinated disclosure window, whichever comes first.

The reporter is asked for a reasonable disclosure delay before public
announcement. No deadline is enforced against a reporter who is cooperating
in good faith.

## Scope

In scope:

- The Python and TypeScript SDKs, the schema contract, the emitter, and the
  Typst CLI adapter.
- The Bazel build rules and code generator, including the template and CSV
  placeholder parser.
- The release workflows, including artifact generation and publication.
- Path handling for assets and modules, including traversal and symlink
  escapes.
- The command invocation of the Typst CLI, including argument handling.

Out of scope:

- Vulnerabilities in the Typst compiler itself. Report those to the Typst
  project.
- Vulnerabilities in Bazel, Python, or Node.js. Report those to the upstream
  project.
- Raw Typst executed by Typcast. Raw Typst is trusted input by design and is
  documented as such in [Security](docs/development/security.md). Applications
  that accept untrusted raw Typst must add an external sandbox.
- Denial of service caused by deliberately enormous inputs to an application
  that does not apply the documented size limits.
- Findings that require a user to already control the local machine or the
  Typcast process.

## Safe harbor

Good-faith security research is welcome. Research that follows this policy is
authorized by the project maintainers. Do not:

- Access data that is not yours.
- Exfiltrate, modify, or delete data.
- Degrade service, including sustained load or resource exhaustion.
- Send spam, phishing, or other unsolicited messages.
- Use social engineering against maintainers or other users.

The maintainers will not pursue legal action against research that follows this
policy. If a rule is unclear, ask for confirmation before acting.

## Security controls in the repository

| Control | State |
|---|---|
| Apache-2.0 license with patent grant | Implemented. |
| Dependency review on pull requests | Required by `CI-015`; implemented in the release workflow. |
| Secret scanning and push protection | Required by `SEC-004`; enabled by repository settings. |
| Automated dependency updates | Required by `SEC-007`; enabled by a dependency update bot. |
| Checksums for release artifacts | Required by `SEC-010`. |
| SBOM for release artifacts | Required by `SEC-025`. |
| Vulnerability response targets | This document. |

Requirements and their verification methods are defined in
[Security](docs/development/security.md) and tracked in
[Requirements traceability](docs/requirements/traceability.md).
