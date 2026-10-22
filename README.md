<h1><img src="https://raw.githubusercontent.com/aleksozolins/orgwarrior-mcp/main/docs/logo.svg" alt="" width="44" align="top"> orgwarrior-mcp</h1>

**A porcelain for Org's agenda, for Claude.** An
[MCP](https://modelcontextprotocol.io) server over
[orgwarrior](https://github.com/aleksozolins/orgwarrior)'s engine: ask
"what's on today?", "push the dentist to Friday" or "what did I get done
this week?", and your running Emacs does the Org work, as it would from
the agenda.

- **Your agenda, as Org builds it**: your views, TODO keywords, tags,
  custom agenda commands, refile targets, logging and repeaters, all as
  in Emacs. Claude reads what `orgwarrior` prints, IDs and all.
- **Act on any task**: states (with a note where Org asks for one), dates,
  tags, priority, effort, properties, notes and its history, its text and
  checklists, renaming, moving, refiling, archiving; add tasks and events
  by fields, so nothing in a title is misread as a date or tag.
- **Look back**: what you finished in any span, the time you clocked, and
  a search of everything you ever archived.
- **Safe by design**: deleting asks you each time, and a task's text is
  never read as instructions.
- **Where Claude has no shell**: claude.ai on the web, the desktop app and
  your phone, through your own server. Any client that speaks MCP works.

## Which one?

**Where Claude can run commands on the machine with your Emacs** (Claude
Code there, or over SSH), give it the
[`orgwarrior`](https://github.com/aleksozolins/orgwarrior) command and the
skill that teaches it (`orgwarrior help --skill`, [With
Claude](https://github.com/aleksozolins/orgwarrior#with-claude)): every
verb, nothing to run as a server, nothing facing the network.

**orgwarrior-mcp is for where it can't**: claude.ai in a browser, the
desktop and phone apps, an MCP client on another machine. They reach your
Emacs through this server and nothing else.

## How it fits

Not a task manager: Org is. In Git's terms Org is the plumbing, and
orgwarrior-mcp a porcelain over it, beside orgwarrior's command line and
[orgwarrior-web](https://github.com/aleksozolins/orgwarrior-web)'s page:

```
  porcelain    orgwarrior       orgwarrior-web       orgwarrior-mcp
               a terminal       a browser            Claude, any MCP client
                       \             |              /
  engine          orgwarrior.el, loaded into your running Emacs
                                 |
  plumbing        Org mode  ──▶  your .org files
```

Claude calls a tool, the server asks the engine, Emacs does the work.
Nothing here reads or writes your Org files itself.

## Tools

| tool | |
|---|---|
| `agenda` | any view `orgwarrior` shows: `today`, `week`, `fri`, `all`, `next +@phone`, a search, your own `[views]`, a file's whole outline, `clocked week`; `archive` takes in the archive files |
| `views` | your named views: your page's tabs and your `[views]`, so "my inbox tab" means what it means to you |
| `done` | what you finished in a span (`week`, `lastweek`, `month`, a date, a range), day by day, archived tasks included |
| `show` | a task in full: where it is, its dates, details, notes and the headings under it |
| `details`, `edit_details` | a task's text as it is in the file, and changing it: a part replaced, or added at the end, refused if it changed since |
| `check` | tick or untick a checkbox, its `[1/3]` following |
| `add_task`, `add_event` | where your `[add]` says, or wherever you say; a task already done (an import) keeps its done date |
| `places`, `files` | where an add can go, your `[add]`'s place first; your agenda files |
| `set_state`, `schedule`, `deadline`, `tag`, `set_priority`, `set_effort`, `set_property`, `add_note`, `rename` | one field each, as Org changes it |
| `history`, `edit_note`, `remove_note` | a task's log (notes, state changes), numbered; changing or deleting one (remove marked destructive) |
| `move`, `reorder` | up, down, promote, demote with the subtree, as M-arrows do; a heading's children in a new order |
| `clock`, `clock_in`, `clock_out` | what's running; clocking in or out now or at a time you forgot |
| `log_time` | time already spent ("an hour on it yesterday at 2"), a running clock left alone |
| `clocks`, `edit_clock`, `remove_clock` | a task's clocks, and fixing or deleting one (remove marked destructive) |
| `refile_targets`, `refile` | your `org-refile-targets`, or into a new heading made there (a new project) |
| `archive`, `kill` | marked destructive; kill lists what would go and deletes only on a second, confirmed call |

The server's instructions carry orgwarrior's own help for views and
dates, so Claude knows the syntax from the start, and say where your
config puts new tasks (an inbox heading, a file's top level, wherever
`[add]` says). Before adding more than a few at once, Claude asks where
they should go.

## Install

On the machine with your Emacs. You need **Emacs 29 or later running as a
daemon** (`emacs --daemon`, or your system's Emacs service) and Python
3.11+. One install gives all three commands, `orgwarrior-mcp`,
`orgwarrior` and `orgwarrior-web` (whose `token` command signs Claude in):

```sh
uv tool install orgwarrior-mcp     # or: pipx install orgwarrior-mcp
```

Update with `uv tool upgrade orgwarrior-mcp` (or `pipx upgrade`), which
brings the other two along. If you installed orgwarrior or orgwarrior-web
on its own first with pipx or uv, uninstall it before: one install carries
all three, one copy of the engine. Beside Homebrew's or the AUR's it works
too, though Emacs then reloads the engine whenever you switch between
them.

## Quick start: claude.ai

claude.ai, its desktop app and the phone apps connect to your server from
Anthropic's cloud, so it needs an address the internet reaches, over
HTTPS. That means a reverse proxy with a real certificate in front of
`orgwarrior-mcp`, which itself stays on 127.0.0.1.

1. **Run it** (as a service: [below](#running-it-as-a-service)):

   ```sh
   orgwarrior-mcp            # http://127.0.0.1:22548/mcp
   ```

2. **Send `/mcp` to it** from your web server. With
   [Caddy](https://caddyserver.com) (it gets the certificate itself):

   ```
   agenda.example.org {
       reverse_proxy /mcp* 127.0.0.1:22548
   }
   ```

   With Apache, in the site's `<VirtualHost *:443>`, before any `ProxyPass /`
   (the first match wins):

   ```apache
   ProxyPass        /mcp http://127.0.0.1:22548/mcp
   ProxyPassReverse /mcp http://127.0.0.1:22548/mcp
   ```

3. **Make Claude a token**:

   ```sh
   orgwarrior-web token add claude --mcp --url https://agenda.example.org
   ```

   It prints the URL and the header to give your client. The token isn't
   shown again; `token revoke claude` cuts it off. Tokens are
   orgwarrior-web's (one file, so `token list` shows Claude's beside your
   devices'), and an `--mcp` token opens this server and nothing of the
   page.

4. **Add the connector**: in claude.ai, Settings → Connectors → Add
   custom connector. The URL is `https://agenda.example.org/mcp`; for
   authentication choose **No sign-in** and leave the OAuth settings
   alone; add the header `Authorization` with the value `Bearer TOKEN`.
   It then works in every conversation, on the web, the desktop app and
   the phone.

Then, in the connector's tool settings, keep `kill` on **needs
approval**, never "always allow": your tap is the check that nothing in a
task's text talked Claude into deleting it.

**With Claude Code too**: a claude.ai connector also shows up in Claude
Code signed in to the same account, beside the `orgwarrior` command if
you use it there. To keep Claude Code on the command line, deny the
connector in `~/.claude/settings.json` (its name as you gave it, spaces as
underscores):

```json
{"permissions": {"deny": ["mcp__claude_ai_orgwarrior"]}}
```

## Other clients

Anything that speaks MCP works, one of two ways:

- **On the machine with Emacs, without a shell** (a desktop app's chat):
  the client runs `orgwarrior-mcp --stdio` itself and talks to it over a
  pipe, nothing on the network and no token. A desktop app usually starts
  it with a bare environment, so give the full path to the command, and
  see [If something's wrong](#if-somethings-wrong) if it can't find Emacs.
  Claude Desktop's `claude_desktop_config.json`, for one:

  ```json
  {"mcpServers": {"orgwarrior": {
      "command": "/home/you/.local/bin/orgwarrior-mcp",
      "args": ["--stdio"]}}}
  ```

- **Over the network**: Streamable HTTP at `https://agenda.example.org/mcp`
  with the header `Authorization: Bearer TOKEN`. A client that takes only
  a URL can carry the token in it: `…/mcp?key=TOKEN`. Keep that URL out
  of your web server's log (Apache: log `%U` instead of `%r`; Caddy logs
  nothing unless you turn logging on).

Claude Code can take either, if you'd rather it used MCP than the
command:

```sh
claude mcp add --scope user orgwarrior -- orgwarrior-mcp --stdio    # on the machine with Emacs
claude mcp add --transport http orgwarrior https://agenda.example.org/mcp \
  --header "Authorization: Bearer TOKEN"                             # from another one
```

## Security

- **A token is the whole sign-in**: one per client, so you can revoke
  each on its own. Only its hash is stored. Requests are logged with the
  token's name and the tool (`claude add_task`), never the token or
  what was sent.
- **Off 127.0.0.1 it won't start without a token.** On 127.0.0.1 it's
  open until the first token is made, for trying it out, and then only
  to requests naming this machine (a web page elsewhere can't reach it by
  pointing its name at 127.0.0.1).
- **Deleting needs you.** `kill` first lists what would go, children
  included, and deletes only on a second call; your client asks you
  before each call. For a task you won't do, a done state keeps it, and
  `archive` puts it away where it can be found (`agenda` with `archive`).
- **Text in your tasks is content, not instructions.** Someone who can
  add to your list (orgwarrior-web's add tokens) can write anything in a
  task's details; Claude is told to read details as content, and deleting
  needs your approval whatever it says.
- **An archived task can be read, not changed**: its ID shows it, and
  every other tool refuses it.

## Running it as a service

On Linux, a systemd user unit (`~/.config/systemd/user/orgwarrior-mcp.service`):

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
loginctl enable-linger "$USER"   # keep it (and Emacs) running when you're logged out
journalctl --user -u orgwarrior-mcp   # who called which tool, when
```

After an upgrade, `systemctl --user restart orgwarrior-mcp`. Tokens and
connectors stay as they are; a client sees new tools at its next
conversation or session.

| option | |
|---|---|
| `--stdio` | MCP on stdin and stdout, for a client that starts the command |
| `--host` | the address to listen on (default `127.0.0.1`) |
| `--port` | default `22548` |
| `-s`, `--socket` | Emacs's server socket, a name or a full path (else orgwarrior's `config.toml`, else the default) |

It reads orgwarrior's `config.toml` (`~/.config/orgwarrior/`) as the
command does: where `add_task` writes, your `[views]`, the socket.

## If something's wrong

- **"no Emacs daemon running on socket 'server'"** while `orgwarrior`
  works in a terminal: the client started `orgwarrior-mcp` with a bare
  environment, without `XDG_RUNTIME_DIR`, where emacsclient looks for the
  socket. Give it the socket's full path: `orgwarrior-mcp --stdio -s
  /run/user/1000/emacs/server` (Emacs tells you its own: `M-:
  (expand-file-name server-name server-socket-dir)`). On macOS also give
  the client a `PATH` with Homebrew's `emacsclient` (`/opt/homebrew/bin`).
- **401 from your server**: no token, a wrong one, or one revoked. `curl
  -i https://agenda.example.org/mcp` should answer 401; a 404 or the
  wrong page means the proxy isn't sending `/mcp` here (put it before
  `/`).
- **"no token yet, and … isn't loopback"**: make one first (`orgwarrior-web
  token add claude --mcp`), or listen on 127.0.0.1 behind the proxy.
- **claude.ai can't connect**: it must reach the URL from the internet,
  with a certificate browsers trust; one from your own CA isn't enough.
- **New tools don't show**: start a new conversation (claude.ai) or
  session (Claude Code, or `/mcp` to reconnect).
- Anything Org refuses (an unknown ID, a date it can't read, a file with
  unsaved changes in Emacs) comes back to Claude as orgwarrior's own
  message, for it to correct.

## Contributing

I read every issue and fix what I can, bugs first. Pull requests are
welcome; for anything big, open an issue first so we can talk it through.
`uv run pytest` runs every test ([Development](#development)).

## Development

```sh
git clone https://github.com/aleksozolins/orgwarrior
git clone https://github.com/aleksozolins/orgwarrior-web
git clone https://github.com/aleksozolins/orgwarrior-mcp
cd orgwarrior-mcp
uv tool install --editable .   # orgwarrior-mcp runs this checkout, the others ../'s
uv run pytest                  # every tool against a throwaway Emacs, over stdio and HTTP
```

The three checkouts sit side by side: orgwarrior-mcp takes orgwarrior and
orgwarrior-web from `../` for development (`[tool.uv.sources]`), from
PyPI when installed. The tests run each
tool against a throwaway `emacs -Q` daemon on orgwarrior's test fixtures:
your own Emacs, config and Org files are never touched.

Claude (Anthropic's AI) was used in developing orgwarrior-mcp. All code
is reviewed by me, and every behavior is covered by real tests.

## License

[GPL-3.0-or-later](https://github.com/aleksozolins/orgwarrior-mcp/blob/main/LICENSE), as Emacs and Org are.
