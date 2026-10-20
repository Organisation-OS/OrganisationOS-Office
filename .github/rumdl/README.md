# Markdown checks

The `check` workflow uses rumdl 0.3.0 for all Markdown linting.
The official rumdl action installs the pinned binary without Node.js or npm.
The linter checks every Git-tracked `.md` file.
The file list comes from `git ls-files`, without recursing into submodules.
Untracked files and dependencies outside Git are not included.

The `.rumdl.toml` configuration uses the default rules and additionally enables
MD070. In particular:

* MD046 detects unclosed fenced code blocks and inconsistent code block styles.
* MD070 detects nested fence collisions. It catches the missing closing fence
  in the changelog before PR 36, even though a later fence closes that block.

The configuration preserves sibling-only duplicate heading checks. It leaves
MD059, MD064, and MD077 disabled to retain the existing link labels, prose
spacing, and list indentation. README and the issue template have explicit
exceptions for their existing layout and long lines. CHANGELOG and README
also retain their existing trailing whitespace; README's missing final newline
is allowed. These exceptions avoid rewriting documents during migration.
MD046 and MD070 remain enabled for every checked file.

MD070 is opt-in, so it must be explicitly enabled. CI does not use automatic
fixes. In particular, MD070
may suggest longer fences, which would not restore an accidentally swallowed
release section.

There is no custom rule forbidding headings or comments inside code. MD070
checks fence collisions, not heading text or release numbers. It does not
detect every case where prose is accidentally included inside a closed block.

To run the same checks locally after installing the pinned version:

```sh
uv tool install rumdl==0.3.0
git ls-files -z -- '*.md' |
  xargs -0 -r rumdl check --config .rumdl.toml --no-cache \
    --deny-config-warnings --
```

The file-list command uses Git Bash on Windows or a POSIX shell on Linux/macOS.
