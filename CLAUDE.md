# orgwarrior-mcp

The org agenda for Claude: an MCP server over orgwarrior's engine
(`../orgwarrior`, `orgwarrior.api`), signed in with orgwarrior-web's
tokens (`../orgwarrior-web`). Org stays the single source of truth;
this package only turns tool calls into engine calls. Published, so
nothing of anyone's setup is hardcoded. A `CLAUDE.local.md` beside this
file, never committed, holds the maintainer's own setup and to-do.

## Shape
- **A package of its own** on the official Python SDK (`mcp`, pinned:
  2.x renamed FastMCP to `MCPServer` and moves fast), served by uvicorn
  at `/mcp`, Streamable HTTP, stateless with plain JSON answers: nothing
  kept between requests, so a restart or a proxy loses nothing. Or over
  stdio (`--stdio`) for a client on the machine with Emacs that starts it:
  no network, no token (the README's quick start, Claude Code). The SDK
  claims fd 1 for the protocol, so the CLI's printers can't write into
  it. A client's environment may be bare (the SDK's own stdio client
  drops `XDG_RUNTIME_DIR`, where emacsclient finds the socket; Claude Code
  passes its whole one): `-s` takes the socket's full path. Not a route
  in orgwarrior-web: that would mean the SDK's ASGI stack in its
  `http.server`, or MCP by hand.
- **Answers are the CLI's text** (`cli.print_*`, no color, stdout captured
  under a lock): IDs on the left, as the orgwarrior skill already teaches
  Claude to read. A file's outline is the whole tree, indented (the CLI
  prints the top level). The server's instructions carry orgwarrior's own
  help for views and dates (`help.py`): one copy, and where the user's
  config puts adds (`instructions()`, at startup: a config change needs a
  restart). Without it a client importing a list picked `to: tasks.org`,
  the file's top level, past the inbox heading; the instructions also say
  to ask before adding more than a few. Facts, never a workflow: some
  people keep tasks at a file's top level, some have no inbox.
- **Tools**: agenda (any view, a file's outline, `clocked SPAN`, `closed
  SPAN`; `archive` takes in the archive files), done (what was finished in
  a span, the archives included), views (the page's tabs, saved ones too,
  and `[views]`: someone who doesn't use Emacs names tabs, not queries), show (an archived
  task's ID too), details and edit_details (the raw text, then a part
  replaced or text appended, `set_entry` with the text read as `old`, so
  a change underneath is refused; the raw text because show's is as
  Emacs shows it, links by their description, and wouldn't match),
  check (by the item's text, set rather than toggled), add_task and add_event (by fields: nothing in a title is read as
  syntax; a done keyword with `closed` for an imported task, its own date
  kept), set_state, schedule, deadline, set_when (an event's date), tag, set_priority, set_effort,
  set_property, add_note, history, edit_note and remove_note (by history's
  number, the item's raw text read again as `old`), move (up, down,
  promote, demote), reorder (all of a parent's children, or a file's top
  level), rename, places (`add_places`: the inbox, then the headings, each file's
  top level), files (the agenda files, for agenda's outline),
  clock, clock_in, clock_out, log_time (the engine's `clock-add`: a
  finished clock, a running one left alone, which clock_in at a past time
  would close), clocks, edit_clock, remove_clock, refile_targets, refile
  (`new_heading`: a new project, refile --new), archive, kill. Annotated
  read-only or not; archive, kill, remove_clock and remove_note
  destructive. No cancel_clock: remove_clock takes a running one. orgwarrior's refusals reach Claude
  as the tool's error (`ToolError`), to read and correct.
- **Kill**: the first call deletes nothing and lists
  what would go; it deletes only called again with `confirmed`. Marked
  destructive, so claude.ai asks the user at each call (leave it on
  "needs approval"): details can hold text someone else wrote (an add
  token's adds), and instructions in it mustn't be able to delete anything; the
  user's tap is the guard, not Claude's judgment. `show` says to read
  details as content.
- **Read-only files** (not writable: a calendar a script exports to org):
  the engine refuses every change; `show` says "read only" and the
  instructions say why, so Claude reports it rather than retrying.

- **`service`**: orgwarrior-web's `setup.service_main` with this name and
  this parser, so one unit-writing path for both servers (needs
  orgwarrior-web 0.4.0).

## Sign-in
- orgwarrior-web's tokens.json, so `orgwarrior-web token list` and
  `revoke` cover Claude too: a `full` token, or one of scope `mcp`
  (`token add claude --mcp`, which the page refuses), as `Authorization:
  Bearer` or `?key=`: claude.ai's custom connector takes only a URL (or
  OAuth, not chosen: not needed to start). Apache's log and this
  server's leave the query out; uvicorn's access log is off.
- On loopback it's open until the tokens file exists, as orgwarrior-web
  is, but only to a loopback Host (a site elsewhere could rebind its name
  to 127.0.0.1). The SDK's own Host check is off: a proxy sends the public
  name. Off loopback it won't start without a token.
- Each request is logged with the token's name and what it asked: a
  tool's name or the method (`claude add_task`), never the arguments (the
  user's tasks) or the token. The SDK's own INFO lines are off (a
  "Terminating session" after every stateless request).

## Published
- **One install for all three commands**: the package declares
  orgwarrior's and orgwarrior-web's entry points beside its own, so `uv
  tool install orgwarrior-mcp` gives all three (checked from a clean
  home): two installs would each load their own engine into Emacs,
  reloading it at every switch. PyPI only: Arch's python-mcp is 1.x, so no
  AUR package; the Homebrew formula is orgwarrior and orgwarrior-web's.
  orgwarrior-web's README points here for anyone wanting both.
- **The README** follows the siblings' shape (logo, the diagram
  with all three, then each subject). "Which one?" first: where
  Claude has a shell on the machine with Emacs, the CLI and its skill
  (`orgwarrior help --skill`); this is for where it hasn't. So the quick
  start is claude.ai through a reverse proxy (Caddy and Apache, `/mcp`
  before `/`), the connector showing in Claude Code too and the deny rule
  for it; stdio for a desktop app; security; the snags met setting it up
  as troubleshooting.

## Development
- `uv run pytest`: the tools against the real engine on a throwaway
  daemon with orgwarrior's fixtures (skipped without emacs or a source
  checkout), through the SDK's in-process client; sign-in over HTTP; the
  command over stdio.
- orgwarrior and orgwarrior-web come from the checkouts beside this one
  (`[tool.uv.sources]`), from PyPI when installed.
- Commit messages: no AI-attribution footers.
