# Changelog

## 0.3.2 (2026-10-24)

- The Install section gives the pipx uninstall command too, and reads more
  simply.

## 0.3.1 (2026-10-24)

Needs orgwarrior 0.4.2.

- The Install section says what to uninstall before installing, rather
  than after, and points to orgwarrior's quick start for setting up Emacs.

## 0.3.0 (2026-10-24)

Needs orgwarrior 0.4.0 and orgwarrior-web 0.4.0.

- **`orgwarrior-mcp service [OPTION…]`** prints a systemd user unit, or a
  launch agent on a Mac, that keeps the server running, with the full
  paths filled in and the steps in comments at the top. It shares
  orgwarrior-web's code, so the two can't drift apart.
- **Plainer messages**: tool errors Claude sees say what to do next ("That
  text isn't in its details. Read details() again"), and so do the
  server's own and its `--help`.
- **The README** is rewritten to be shorter and clearer. It points to
  `orgwarrior --check` for checking your setup, and its service section
  uses the new command.

## 0.2.1 (2026-10-23)

Needs orgwarrior 0.3.0.

- **Read-only files**: Claude is told what a task marked "read only" is (a
  task in a file that isn't writable, usually a copy of another calendar)
  and that changes to it are refused, so it tells you instead of trying
  again.

## 0.2.0 (2026-10-22)

Needs orgwarrior 0.2.0.

- `set_when`: change or remove an event's date.

## 0.1.0 (2026-10-22)

- First public release.
