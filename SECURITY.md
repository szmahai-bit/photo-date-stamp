# Security Policy

## Supported versions

This is a small desktop utility with no server component. We generally support the latest release only.

| Version | Supported |
| ------- | --------- |
| 1.0.x   | ✅        |

## Reporting a vulnerability

If you find a security issue, please **do not** open a public issue. Instead, contact the maintainer privately via GitHub's "Report a vulnerability" feature on the Security tab, or open a draft security advisory.

Please include:

- A description of the issue and its impact
- Steps to reproduce
- Affected version / platform
- Any suggested mitigation

You can expect an acknowledgement within a reasonable time. We will work with you on a fix and coordinate disclosure.

## Scope notes

- The tool runs entirely locally and makes no network requests.
- It reads the image files you explicitly add and writes output to a folder you choose.
- The prebuilt EXE is unsigned; on some systems SmartScreen/AV may warn. Build from source if you prefer to audit the code yourself (see README).
