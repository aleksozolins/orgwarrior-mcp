"""The tools against the real engine, on a throwaway daemon with
orgwarrior's fixtures, through the SDK's own client; and signing in, over
HTTP.  Skipped unless emacs is installed and orgwarrior is a source
checkout (its tests/ holds the fixtures)."""

import asyncio
import json
import re
import os
import shutil
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import httpx2
import orgwarrior
import pytest
import uvicorn
from mcp import Client
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from orgwarrior import OrgwarriorError
from orgwarrior.api import Orgwarrior
from orgwarrior.config import Config
from orgwarrior_web.auth import Tokens

from orgwarrior_mcp.server import instructions, make_app, make_server, startup_places

FIXTURES = Path(orgwarrior.__file__).resolve().parents[2] / "tests"


@pytest.fixture
def ow(tmp_path):
    if not shutil.which("emacs") or not (FIXTURES / "fixture-init.el").exists():
        pytest.skip("needs emacs and orgwarrior's fixtures (a source checkout)")
    name, org = f"orgwarrior-mcp-test-{uuid.uuid4().hex[:8]}", tmp_path / "org"
    env = {**os.environ, "ORGWARRIOR_FIXTURE_DEST": str(org)}
    env.pop("ALTERNATE_EDITOR", None)  # no daemon -> emacsclient would launch it
    subprocess.run(["emacs", "-Q", f"--daemon={name}", "-l", str(FIXTURES / "fixture-init.el")],
                   env=env, check=True, capture_output=True, timeout=30)
    try:
        yield Orgwarrior(Config(add_file=str(org / "inbox.org"), add_heading="Tasks"), name)
    finally:
        subprocess.run(["emacsclient", "-s", name, "-e", "(kill-emacs)"], capture_output=True, env=env)


def calls(server, *steps):
    """Each (tool, arguments) in turn, on one connection: [(text, is_error)]."""
    async def go():
        async with Client(server) as c:
            out = []
            for name, args in steps:
                r = await c.call_tool(name, args)
                out.append(("\n".join(p.text for p in r.content), r.is_error))
            return out
    return asyncio.run(go())


def id_of(text: str, title: str) -> str:
    return next(l.split()[0] for l in text.splitlines() if title in l)


def test_tools(ow):
    server = make_server(ow)
    [(all_, err)] = calls(server, ("agenda", {"query": "all"}))
    assert not err and "Pay rent" in all_
    rent = id_of(all_, "Pay rent")
    [(shown, _), (bad, bad_err), (outline, _), (nope, nope_err)] = calls(
        server, ("show", {"ids": [rent]}), ("show", {"ids": ["zzzz"]}),
        ("agenda", {"query": "projects.org"}), ("agenda", {"query": f"{rent} done"}))
    assert shown.startswith(rent) and "Pay rent" in shown
    assert bad_err and "zzzz" in bad  # orgwarrior's own message, for Claude to read
    assert "Orgwarrior" in outline
    assert nope_err and "Not a view" in nope  # actions have tools of their own

    # Added by fields: nothing in the title is read as a date or tag.
    [(added, err)] = calls(server, ("add_task", {"title": "Buy paint fri :x:", "keyword": "NEXT",
                                                 "scheduled": "+2d", "tags": ["@home"]}))
    assert not err and "NEXT Buy paint fri :x:" in added and ":@home:" in added
    paint = added.split()[0]
    [(task, _)] = calls(server, ("show", {"ids": [paint]}))
    assert "SCHEDULED:" in task and "inbox.org" in task

    steps = calls(server, ("deadline", {"ids": [paint], "date": "+1w"}),
                  ("tag", {"ids": [paint], "add": ["urgent"], "remove": ["@home"]}),
                  ("set_priority", {"ids": [paint], "priority": "A"}),
                  ("add_note", {"ids": [paint], "text": "the blue one"}),
                  ("set_state", {"ids": [paint], "keyword": "wait"}),
                  ("show", {"ids": [paint]}))
    assert not any(e for _, e in steps), steps
    final = steps[-1][0]
    assert "DEADLINE:" in final and ":urgent:" in final and "@home" not in final
    assert "[#A]" in final and "WAIT" in final and "the blue one" in final

    # A new ID after a rename, shown as old → new.
    [(renamed, _)] = calls(server, ("rename", {"id": paint, "title": "Buy blue paint"}))
    assert "→" in renamed
    paint = renamed.split("→")[1].split()[0]
    [(targets, _), (refiled, _)] = calls(server, ("refile_targets", {"ids": [paint]}),
                                         ("refile", {"ids": [paint], "target": "projects.org"}))
    assert "projects.org" in targets and "→" in refiled
    paint = refiled.split("→")[1].split()[0]
    [(archived, err), (gone, gone_err)] = calls(server, ("archive", {"ids": [paint]}),
                                                ("show", {"ids": [paint]}))
    assert not err and "_archive" in archived and gone_err

    [(event, err)] = calls(server, ("add_event", {"title": "Dentist", "when": "fri 10:30"}))
    assert not err and "Dentist" in event
    dentist = event.split()[0]
    [(moved, err), (shown, _)] = calls(server, ("set_when", {"ids": [dentist], "date": "2026-12-26 11:00"}),
                                       ("show", {"ids": [dentist]}))
    assert not err and "<2026-12-26 Sat 11:00>" in shown and "SCHEDULED" not in shown


def test_kill(ow):
    server = make_server(ow)
    async def kill_tool():
        async with Client(server) as c:
            return next(t for t in (await c.list_tools()).tools if t.name == "kill")
    assert asyncio.run(kill_tool()).annotations.destructive_hint  # the client asks the user
    [(all_, _)] = calls(server, ("agenda", {"query": "all"}))
    juggle = id_of(all_, "Learn to juggle")
    # First a list of what would go, nothing deleted; then, confirmed, gone.
    [(asked, err), (still, _), (killed, kerr), (gone, gone_err)] = calls(
        server, ("kill", {"ids": [juggle]}), ("show", {"ids": [juggle]}),
        ("kill", {"ids": [juggle], "confirmed": True}), ("show", {"ids": [juggle]}))
    assert not err and "Nothing deleted" in asked and "Learn to juggle" in asked
    assert "Learn to juggle" in still
    assert not kerr and "(deleted)" in killed and gone_err


def test_done_and_archives(ow):
    server = make_server(ow)
    [(all_, _)] = calls(server, ("agenda", {"query": "all"}))
    juggle = id_of(all_, "Learn to juggle")
    calls(server, ("set_state", {"ids": [juggle], "keyword": "done", "note": "Did it"}),
          ("archive", {"ids": [juggle]}))
    [(done, err), (live, _), (archived, _), (old, old_err)] = calls(
        server, ("done", {"span": "week"}), ("agenda", {"query": "juggle"}),
        ("agenda", {"query": "juggle", "archive": True}), ("done", {"span": "soon"}))
    assert not err and "DONE Learn to juggle" in done
    assert "(no tasks)" in live and "Learn to juggle" in archived
    assert old_err and "Not a span" in old
    [(shown, _)] = calls(server, ("show", {"ids": [id_of(done, "juggle")]}))
    assert "tasks.org_archive" in shown


def serve(app) -> tuple[str, uvicorn.Server]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    while not server.started:
        time.sleep(0.05)
    return f"http://127.0.0.1:{port}/mcp", server


def post(url, headers=None):
    req = urllib.request.Request(url, data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json, text/event-stream", **(headers or {})})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def over_http(url, token=None):
    """The agenda tool over HTTP, as Claude calls it."""
    async def go():
        http = httpx2.AsyncClient(headers={"Authorization": f"Bearer {token}"} if token else {})
        async with Client(streamable_http_client(url, http_client=http)) as c:
            r = await c.call_tool("agenda", {"query": "all"})
            return r.content[0].text
    return asyncio.run(go())


def test_sign_in(ow, tmp_path, capfd):
    tokens = Tokens(tmp_path / "tokens.json")
    url, server = serve(make_app(ow, "127.0.0.1", tokens))
    try:
        # Loopback, no tokens file yet: open, but only by this machine's name.
        assert "Pay rent" in over_http(url)
        assert post(url, {"Host": "evil.example"}) == 403
        claude, me, robin = tokens.add("claude", "mcp"), tokens.add("phone"), tokens.add("robin", "add")
        assert post(url) == 401
        assert post(url, {"Authorization": "Bearer wrong"}) == 401
        assert post(url, {"Authorization": f"Bearer {robin}"}) == 401  # an add token sees nothing
        assert "Pay rent" in over_http(url, claude) and "Pay rent" in over_http(url, me)
        assert post(f"{url}?key={claude}") == 200  # claude.ai's connector: a URL only
        assert post(f"{url}?key={robin}") == 401
        # A proxy's Host goes through once signed in.
        assert post(url, {"Authorization": f"Bearer {claude}", "Host": "ow.example.org"}) == 200
        tokens.revoke("claude")
        assert post(url, {"Authorization": f"Bearer {claude}"}) == 401
        assert post(f"{url}?key={claude}") == 401
    finally:
        server.should_exit = True
    # Each request as the token's name and what it asked: a tool's name, not its arguments.
    log = capfd.readouterr().err.splitlines()
    assert "claude agenda" in log and "phone agenda" in log and "claude ping" in log
    assert not any("all" in l.split()[1:] or "Terminating" in l or claude in l for l in log), log


def test_off_loopback_needs_a_token(ow, tmp_path):
    with pytest.raises(OrgwarriorError, match="no token yet"):
        make_app(ow, "0.0.0.0", Tokens(tmp_path / "tokens.json"))


def test_stdio(ow):
    """As a local client runs it: the command, MCP on its stdin and stdout."""
    # The SDK's default environment leaves out XDG_RUNTIME_DIR, where emacsclient finds the socket.
    params = StdioServerParameters(command="uv", args=["run", "orgwarrior-mcp", "--stdio", "-s", ow.socket],
                                   cwd=str(Path(__file__).parents[1]), env=dict(os.environ))
    async def go():
        async with Client(stdio_client(params)) as c:
            return (await c.call_tool("agenda", {"query": "all"})).content[0].text
    assert "Pay rent" in asyncio.run(go())


def test_details_and_checkboxes(ow):
    server = make_server(ow)
    rent = id_of(calls(server, ("agenda", {"query": "all"}))[0][0], "Pay rent")
    [(text, _)] = calls(server, ("details", {"id": rent}))
    assert text.startswith("DEADLINE:") and "Transfer from checking." in text  # as in the file
    steps = calls(server,
                  ("edit_details", {"id": rent, "old_text": "from checking", "new_text": "from savings"}),
                  ("edit_details", {"id": rent, "new_text": "- [ ] ask the landlord"}),
                  ("check", {"id": rent, "item": "memo"}),
                  ("check", {"id": rent, "item": "memo"}),
                  ("details", {"id": rent}))
    assert not any(e for _, e in steps), steps
    assert "Details saved" in steps[0][0] and "[1/2]" in steps[2][0] and "Already ticked" in steps[3][0]
    final = steps[-1][0]
    assert final.startswith("DEADLINE:") and "Transfer from savings." in final
    assert "- [X] remember the memo line\n- [ ] ask the landlord" in final
    [(missing, m_err), (none, n_err)] = calls(
        server, ("edit_details", {"id": rent, "old_text": "from checking", "new_text": "x"}),
        ("check", {"id": rent, "item": "groceries"}))
    assert m_err and "read details() again" in missing
    assert n_err and "ask the landlord" in none  # the boxes it has, listed


def test_views_and_new_heading(ow, tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))
    (tmp_path / "orgwarrior-web").mkdir()
    (tmp_path / "orgwarrior-web/tabs.json").write_text(json.dumps([{"label": "home", "query": "+@home"}]))
    server = make_server(ow)
    [(views, _)] = calls(server, ("views", {}))
    assert views.splitlines()[0].split() == ["today", "today"] and ["home", "+@home"] in [
        l.split() for l in views.splitlines()]
    rent = id_of(calls(server, ("agenda", {"query": "all"}))[0][0], "Pay rent")
    [(moved, err), (outline, _)] = calls(
        server, ("refile", {"ids": [rent], "target": "projects.org", "new_heading": "Money"}),
        ("agenda", {"query": "projects.org"}))
    assert not err and "→" in moved
    assert re.search(r"\n\S+  Money\n  \S+  TODO Pay rent", "\n" + outline)


def test_files_and_clocks(ow):
    # Clocking relative to now in several calls: a minute passing between
    # them would add one to org's whole-minute clock lines.
    if (second := time.localtime().tm_sec) >= 50:
        time.sleep(60.2 - second)
    server = make_server(ow)
    [(files, _)] = calls(server, ("files", {}))
    assert sorted(files.splitlines()) == ["calendar.org", "inbox.org", "projects.org", "tasks.org"]
    juggle = id_of(calls(server, ("agenda", {"query": "all"}))[0][0], "Learn to juggle")
    steps = calls(server,
                  ("clock", {}),
                  ("clock_in", {"id": juggle, "time": "-30m"}),
                  ("log_time", {"id": juggle, "start": "2026-10-05 9:40", "end": "12:23"}),
                  ("log_time", {"id": juggle, "start": "2026-10-06 14:05", "duration": "42m"}),
                  ("clock", {}),
                  ("clocks", {"id": juggle}),
                  ("edit_clock", {"id": juggle, "n": 3, "start": "9:30"}),
                  ("remove_clock", {"id": juggle, "n": 2}),
                  ("clock_out", {}))
    assert not any(e for _, e in steps), steps
    assert steps[0][0] == "No clock running."
    assert "clocked in at" in steps[1][0]
    assert "running" in steps[2][0] and "09:40–12:23  2:43" in steps[2][0]  # the running clock left alone
    assert "running 0:30" in steps[4][0]
    assert [l.split()[0] for l in steps[5][0].splitlines()[1:4]] == ["1", "2", "3"]
    assert "09:30–12:23  2:53" in steps[6][0]
    assert "14:05" not in steps[7][0]
    assert "clocked out at" in steps[8][0]
    [(_, both), (_, later)] = calls(server,
                                    ("log_time", {"id": juggle, "start": "9:00", "end": "10:00", "duration": "1h"}),
                                    ("log_time", {"id": juggle, "start": "-10m", "duration": "1h"}))
    assert both and later


def test_adding(ow):
    # The instructions say where adds go, from the config: no file to pick.
    said = lambda *a: " ".join(instructions(*a).split())  # unwrapped
    assert "puts a task in inbox.org › Tasks, where the" in said(ow.config)
    assert "usual place" not in said(Config(refile_usual="tasks"))  # named none of the places
    assert "puts a task in tasks.org (its top level)" in said(Config(add_file="/x/tasks.org"))
    assert "org-default-notes-file" in said(Config())
    assert 'usual place to file a task is "tasks.org › Tasks"' in said(
        Config(refile_usual="tasks"), "tasks.org › Tasks")
    assert startup_places(ow)["task"] == "inbox.org › Tasks"
    ow.config.refile_usual = "nowhere"
    assert startup_places(ow)["usual"] is None
    ow.config.refile_usual = "projects"
    assert startup_places(ow)["usual"] == "projects.org"
    assert "in gtd/inbox.org (its top level)" in said(Config(), None, "gtd/inbox.org")  # the engine's name
    server = make_server(ow)
    ow.config.event_file = str(Path(ow.config.add_file).with_name("calendar.org"))
    [(places, _), (events, _)] = calls(server, ("places", {}), ("places", {"event": True}))
    assert events.splitlines()[0] == "calendar.org"
    assert places.splitlines()[0] == "inbox.org › Tasks" and "tasks.org" in places.splitlines()
    # A finished task, as an import brings it: done, on the day it was.
    [(added, err), (closed_open, open_err)] = calls(
        server, ("add_task", {"title": "Old one", "keyword": "DONE", "closed": "2026-03-02 09:15"}),
        ("add_task", {"title": "x", "closed": "2026-03-02"}))
    assert not err and "DONE Old one" in added
    [(shown, _)] = calls(server, ("show", {"ids": [added.split()[0]]}))
    assert "CLOSED: [2026-03-02 Mon 09:15]" in shown
    assert open_err and "done keyword" in closed_open


def test_more_tools(ow):
    server = make_server(ow)
    all_ = calls(server, ("agenda", {"query": "all"}))[0][0]
    juggle = id_of(all_, "Learn to juggle")
    steps = calls(server,
                  ("set_effort", {"ids": [juggle], "effort": "1:30"}),
                  ("set_property", {"ids": [juggle], "name": "LOCATION", "value": "the park"}),
                  ("show", {"ids": [juggle]}),
                  ("set_property", {"ids": [juggle], "name": "LOCATION"}),
                  ("add_note", {"ids": [juggle], "text": "three balls first"}),
                  ("history", {"id": juggle}))
    assert not any(e for _, e in steps), steps
    assert "Learn to juggle" in steps[0][0]
    assert ":PROPERTIES: (2 lines)" in steps[2][0]  # Effort and LOCATION, before it's removed
    shown = calls(server, ("details", {"id": juggle}))[0][0]
    assert re.search(r":Effort:\s+1:30", shown, re.I)
    assert "LOCATION" not in shown  # removed again
    assert steps[5][0].startswith("1  Note taken on") and "three balls first" in steps[5][0]
    [(edited, err), (removed, rerr), (gone, gerr)] = calls(
        server, ("edit_note", {"id": juggle, "n": 1, "text": "four balls"}),
        ("remove_note", {"id": juggle, "n": 1}), ("edit_note", {"id": juggle, "n": 9, "text": "x"}))
    assert not err and "four balls" in edited and not rerr and "four balls" not in removed
    assert gerr and "history()" in gone
    # Moving: a heading's children in a new order, then one past a sibling.
    project = id_of(calls(server, ("agenda", {"query": "projects.org"}))[0][0], "Orgwarrior")
    kids = lambda: [l.split()[0] for l in calls(server, ("show", {"ids": [project]}))[0][0]
                    .split("Outline", 1)[1].splitlines() if l.strip()]
    before = kids()
    [(_, bad), (reordered, rerr)] = calls(server, ("move", {"ids": [before[0]], "direction": "sideways"}),
                                         ("reorder", {"ids": before[::-1], "parent": project}))
    assert bad and not rerr, reordered
    assert kids() == before[::-1]
    [(moved, merr)] = calls(server, ("move", {"ids": [before[0]], "direction": "up"}))
    assert not merr, moved
    assert kids()[-2] == before[0]
    [(_, neither)] = calls(server, ("reorder", {"ids": before}))
    assert neither
