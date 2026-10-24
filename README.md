<h1><img src="https://raw.githubusercontent.com/aleksozolins/orgwarrior-mcp/main/docs/logo.svg" alt="" width="44" align="top"> orgwarrior-mcp</h1>

[![tests](https://github.com/aleksozolins/orgwarrior-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/aleksozolins/orgwarrior-mcp/actions/workflows/ci.yml)

Your org agenda for Claude. It's an [MCP](https://modelcontextprotocol.io)
server on top of [orgwarrior](https://github.com/aleksozolins/orgwarrior).
Ask "what's on today?", "push the dentist to Friday" or "what did I get
done this week?", and your running Emacs does the org work, the same as it
would from the agenda.

- **Your agenda, the way org builds it.** Your views, TODO keywords, tags,
  custom agenda commands, refile targets, logging and repeaters all work
  as they do in Emacs. Claude reads what `orgwarrior` prints, IDs
  included.
- **Change anything about a task.** States (with a note where org asks for
  one), dates, tags, priority, effort, properties, notes and history, its
  text and checklists. Claude can also rename, move, refile and archive
  tasks, and add tasks and events. Adds go in as separate fields, so
  nothing in a title gets mistaken for a date or a tag.
- **Look back.** Ask what you finished in any span, how much time you
  clocked, or search everything you've ever archived.
- **Safe by design.** Deleting asks you every time, and a task's text is
  never treated as instructions.
- **Works where Claude has no shell**: claude.ai on the web, the desktop
  app and your phone, through your own server. Any client that speaks MCP
  works too.

## Which one do you need?

**If Claude can run commands on the machine with your Emacs** (Claude
Code there, or over SSH), use the
[`orgwarrior`](https://github.com/aleksozolins/orgwarrior) command and its
skill (`orgwarrior help --skill`, see
[With Claude](https://github.com/aleksozolins/orgwarrior#with-claude)).
It has every command, and there's no server to run or expose to the
network.

**orgwarrior-mcp is for when it can't**: claude.ai in a browser, the
desktop and phone apps, or an MCP client on another machine. They reach
your Emacs through this server and nothing else.

## How it fits

Org is the task manager. orgwarrior-mcp is a friendlier way in, alongside
orgwarrior's command line and
[orgwarrior-web](https://github.com/aleksozolins/orgwarrior-web)'s page:

```
  orgwarrior          orgwarrior-web         orgwarrior-mcp
  (a terminal)        (a browser)            (Claude, any MCP client)
          \                 |                 /
       orgwarrior.el, loaded into your running Emacs
                            |
             Org mode  ──▶  your .org files
```

Claude calls a tool, the server passes it to Emacs, and Emacs does the
work. The server never reads or writes your org files itself.

## Tools

| tool | what it does |
|---|---|
| `agenda` | shows any view `orgwarrior` can: `today`, `week`, `fri`, `all`, `next +@phone`, a search, your own `[views]`, a file's whole outline, `clocked week`. With `archive`, it includes archived tasks. |
| `views` | lists your named views (your page's tabs and your `[views]`), so "my inbox tab" means what it means to you |
| `done` | lists what you finished in a span (`week`, `lastweek`, `month`, a date, a range), day by day, archived tasks included |
| `show` | shows a task in full: where it is, its dates, text, notes and the headings under it |
| `details`, `edit_details` | reads a task's text as it is in the file, and changes it by replacing a part or adding to the end. A change is refused if the text changed in the meantime. |
| `check` | ticks or unticks a checkbox and updates its `[1/3]` |
| `add_task`, `add_event` | adds where your `[add]` says, or wherever you ask. A task added as already done (an import) keeps its done date. |
| `places`, `files` | lists where an add can go (your `[add]` place first), and your agenda files |
| `set_state`, `schedule`, `deadline`, `set_when` (an event's date), `tag`, `set_priority`, `set_effort`, `set_property`, `add_note`, `rename` | each changes one field, the way org does |
| `history`, `edit_note`, `remove_note` | lists a task's log (notes and state changes) by number, and changes or deletes an entry. `remove_note` is marked destructive. |
| `move`, `reorder` | moves a task up, down, in or out with its subtree, like org's M-arrows, or puts a heading's children in a new order |
| `clock`, `clock_in`, `clock_out` | shows what's running, and clocks in or out now or at a time you forgot |
| `log_time` | logs time already spent ("an hour on it yesterday at 2") without touching a running clock |
| `clocks`, `edit_clock`, `remove_clock` | lists a task's clocks, and fixes or deletes one. `remove_clock` is marked destructive. |
| `refile_targets`, `refile` | lists your `org-refile-targets`, and refiles to one, or into a new heading made there (for a new project) |
| `archive`, `kill` | both marked destructive. `kill` first lists what would be deleted, and only deletes on a second, confirmed call. |

The server's instructions include orgwarrior's own help for views and
dates, so Claude knows the syntax from the start. They also say where your
config puts new tasks (an inbox heading, a file's top level, or wherever
`[add]` points). Before adding more than a few tasks at once, Claude asks
where they should go.

## Install

Install it on the machine with your Emacs. You'll need Emacs 29 or later
running as a daemon (`emacs --daemon`, or your system's Emacs service), and
Python 3.11 or later. One install gives you all three commands:
`orgwarrior-mcp`, `orgwarrior`, and `orgwarrior-web` (its `token` command
signs Claude in).

```sh
uv tool install orgwarrior-mcp     # or: pipx install orgwarrior-mcp
```

To update, run `uv tool upgrade orgwarrior-mcp` (or `pipx upgrade
orgwarrior-mcp`), which updates the other two as well. If you installed
orgwarrior or orgwarrior-web on its own first with pipx or uv, uninstall
it before installing this, since this one brings its own copy. It also
works alongside the Homebrew or AUR packages, but Emacs then reloads
orgwarrior's code whenever you switch between them.

## Quick start: claude.ai

claude.ai, its desktop app and the phone apps connect to your server from
Anthropic's cloud. That means your server needs an address the internet
can reach, over HTTPS, so you'll need a reverse proxy with a real
certificate in front of `orgwarrior-mcp`. The server itself stays on
127.0.0.1.

1. **Run it** (to keep it running, see [below](#running-it-as-a-service)):

   ```sh
   orgwarrior-mcp            # http://127.0.0.1:22548/mcp
   ```

2. **Point your web server's `/mcp` at it.** With
   [Caddy](https://caddyserver.com), which gets the certificate for you:

   ```
   agenda.example.org {
       reverse_proxy /mcp* 127.0.0.1:22548
   }
   ```

   With Apache, put this in the site's `<VirtualHost *:443>`, before any
   `ProxyPass /` (the first match wins):

   ```apache
   ProxyPass        /mcp http://127.0.0.1:22548/mcp
   ProxyPassReverse /mcp http://127.0.0.1:22548/mcp
   ```

3. **Make a token for Claude**:

   ```sh
   orgwarrior-web token add claude --mcp --url https://agenda.example.org
   ```

   It prints the URL and the header to give your client. The token is
   shown only this once, and `token revoke claude` cuts it off. Tokens
   live in orgwarrior-web's tokens file, so `token list` shows Claude's
   next to your devices'. An `--mcp` token only opens this server, not the
   web page.

4. **Add the connector.** In claude.ai, go to Settings → Connectors → Add
   custom connector. The URL is `https://agenda.example.org/mcp`. For
   authentication choose **No sign-in** and leave the OAuth settings
   alone, then add a header named `Authorization` with the value
   `Bearer TOKEN`. It works in every conversation from then on, on the
   web, the desktop app and the phone.

Then, in the connector's tool settings, keep `kill` on **needs
approval**, never "always allow". Your tap is the check that nothing in a
task's text talked Claude into deleting it.

**If you also use Claude Code**: a claude.ai connector shows up in Claude
Code too, when it's signed in to the same account, next to the
`orgwarrior` command if you use that. To keep Claude Code on the command
line, deny the connector in `~/.claude/settings.json`. Use the name you
gave the connector, with spaces as underscores:

```json
{"permissions": {"deny": ["mcp__claude_ai_orgwarrior"]}}
```

## Other clients

Anything that speaks MCP can connect in one of two ways:

- **On the machine with Emacs, without a shell** (a desktop app's chat,
  for example): the client runs `orgwarrior-mcp --stdio` itself and talks
  to it over a pipe. Nothing goes over the network and no token is
  needed. Desktop apps usually start it with a bare environment, so give
  the command's full path, and see [Troubleshooting](#troubleshooting) if
  it can't find Emacs. For example, in Claude Desktop's
  `claude_desktop_config.json`:

  ```json
  {"mcpServers": {"orgwarrior": {
      "command": "/home/you/.local/bin/orgwarrior-mcp",
      "args": ["--stdio"]}}}
  ```

- **Over the network**: Streamable HTTP at `https://agenda.example.org/mcp`
  with the header `Authorization: Bearer TOKEN`. A client that only takes
  a URL can carry the token in it: `…/mcp?key=TOKEN`. Keep that URL out of
  your web server's log. In Apache, log `%U` instead of `%r`. Caddy logs
  nothing unless you turn logging on.

Claude Code can use either, if you'd rather it used MCP than the command:

```sh
claude mcp add --scope user orgwarrior -- orgwarrior-mcp --stdio    # on the machine with Emacs
claude mcp add --transport http orgwarrior https://agenda.example.org/mcp \
  --header "Authorization: Bearer TOKEN"                             # from another machine
```

## Security

- **A token is the whole sign-in.** Make one per client, so you can revoke
  each one separately. Only a hash of it is stored. Requests are logged
  with the token's name and the tool (`claude add_task`), never the token
  or what was sent.
- **It won't listen on anything but 127.0.0.1 without a token.** On
  127.0.0.1 it's open until you create the first token, so you can try it
  out. While it's open, it only answers requests addressed to this
  machine by name, so a web page elsewhere can't reach it by pointing a
  domain at 127.0.0.1.
- **Deleting needs you.** `kill` first lists what would be deleted,
  children included, and only deletes on a second call. Your client asks
  you before each call. For a task you won't do, a done state keeps it,
  and `archive` puts it away where you can still find it (`agenda` with
  `archive`).
- **Text in your tasks is content, not instructions.** Anyone who can add
  to your list (with an orgwarrior-web add token) can write anything in a
  task's text. Claude is told to treat it as content, and deleting needs
  your approval no matter what the text says.
- **Archived tasks are read only.** Their ID marks them as archived, and
  every tool that changes things refuses them.

## Running it as a service

On Linux, use a systemd user unit. Save this as
`~/.config/systemd/user/orgwarrior-mcp.service`:

```ini
[Unit]
Description=orgwarrior-mcp
After=emacs.service
Wants=emacs.service

[Service]
ExecStart=%h/.local/bin/orgwarrior-mcp
Restart=on-failure

[Install]
WantedBy=default.target
```

```sh
systemctl --user enable --now orgwarrior-mcp
loginctl enable-linger "$USER"   # keeps it (and Emacs) running when you're logged out
journalctl --user -u orgwarrior-mcp   # who called which tool, and when
```

After an upgrade, run `systemctl --user restart orgwarrior-mcp`. Tokens
and connectors stay as they are, and a client sees new tools in its next
conversation or session.

| option | what it does |
|---|---|
| `--stdio` | speaks MCP on stdin and stdout, for a client that starts the command itself |
| `--host` | the address to listen on (default `127.0.0.1`) |
| `--port` | the port (default `22548`) |
| `-s`, `--socket` | Emacs's server socket, as a name or a full path. Otherwise it uses orgwarrior's `config.toml`, or the default. |

It reads orgwarrior's `config.toml` (in `~/.config/orgwarrior/`) the same
way the command does, for where `add_task` writes, your `[views]`, and
the socket.

## Troubleshooting

- **"no Emacs daemon running on socket 'server'"**, while `orgwarrior`
  works in a terminal: the client started `orgwarrior-mcp` with a bare
  environment, missing `XDG_RUNTIME_DIR`, which is where emacsclient looks
  for the socket. Give it the socket's full path, like
  `orgwarrior-mcp --stdio -s /run/user/1000/emacs/server`. Emacs can tell
  you its own with `M-: (expand-file-name server-name server-socket-dir)`.
  On macOS, also give the client a `PATH` that includes Homebrew's
  `emacsclient` (`/opt/homebrew/bin`).
- **401 from your server**: the token is missing, wrong, or revoked.
  `curl -i https://agenda.example.org/mcp` should answer 401. If you get a
  404 or the wrong page, the proxy isn't sending `/mcp` here. Put its rule
  before the one for `/`.
- **"no token yet, and … isn't loopback"**: create a token first
  (`orgwarrior-web token add claude --mcp`), or listen on 127.0.0.1 behind
  the proxy.
- **claude.ai can't connect**: it has to reach the URL from the internet,
  with a certificate browsers trust. A certificate from your own CA isn't
  enough.
- **New tools don't show up**: start a new conversation (claude.ai) or
  session (Claude Code, or run `/mcp` to reconnect).
- Anything org refuses, like an unknown ID, a date it can't read, a file
  with unsaved changes in Emacs, or a read-only file such as an exported
  calendar, goes back to Claude as orgwarrior's own error message, so it
  can correct itself.

## Contributing

I read every issue and fix what I can, bugs first. Pull requests are
welcome. For anything big, open an issue first so we can talk it through.
`uv run pytest` runs every test ([Development](#development)).

## Development

```sh
git clone https://github.com/aleksozolins/orgwarrior
git clone https://github.com/aleksozolins/orgwarrior-web
git clone https://github.com/aleksozolins/orgwarrior-mcp
cd orgwarrior-mcp
uv tool install --editable .   # orgwarrior-mcp runs this checkout, the other two run theirs
uv run pytest                  # every tool against a throwaway Emacs, over stdio and HTTP
```

Keep the three checkouts side by side. For development, orgwarrior-mcp
uses orgwarrior and orgwarrior-web from `../` (`[tool.uv.sources]`).
Installed, it uses the releases from PyPI. The tests run each tool against
a throwaway `emacs -Q` daemon on orgwarrior's test files, so your own
Emacs, config and org files are never touched.

Claude (Anthropic's AI) was used in developing orgwarrior-mcp. I review
all the code, and every behavior is covered by tests.

## License

[GPL-3.0-or-later](https://github.com/aleksozolins/orgwarrior-mcp/blob/main/LICENSE), the same as Emacs and Org.
