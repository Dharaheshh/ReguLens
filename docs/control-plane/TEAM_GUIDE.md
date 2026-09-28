# TEAM_GUIDE.md — ReguLens Team Guide (Docker, Git, Who's Building What)

Read this once, all three of you. This is your map of the project, who owns
what, and exactly when to merge into `main`.

Repo: **Regulens**

---

## PART 0 — What we're actually building, in one paragraph

ReguLens takes a regulator's question, finds real evidence in our document
library, drafts an answer where every sentence is backed by a real,
click-through-checkable citation, checks that answer doesn't contradict
anything we've said before, and tells us honestly when we don't have enough
evidence to answer at all — then a human approves it before it counts as
final. Full detail lives in `docs/control-plane/PROJECT_CONTEXT.md` and
`ARCHITECTURE.md` if anyone wants the deep version. This file is just: who's
building what, and how we don't step on each other.

---

## PART 0.5 — Who's building what

| Person | Owns | In plain English | Tasks (see `TASKS.md`) |
|---|---|---|---|
| **Dharaheshh** | `main` branch + Generation & Validation engines | Owns the repo's main timeline (reviews and merges everyone's PRs). Also builds the "brain" of the system: turning a query into requirements, drafting the response with citations, checking if a claim overclaims, checking if it contradicts something we said before, and deciding if we have enough evidence at all. | **TASK-011 → TASK-017** |
| **Harieshvaran** | Ingestion & Retrieval | Builds the part that takes an uploaded PDF and makes it searchable: reading the PDF, splitting it into chunks, turning those chunks into searchable data, and building the actual search (so a question like "microbiological safety" can find the right paragraph). | **TASK-005 → TASK-009** |
| **Akshay** | Frontend (the screens people actually see) | Builds the pages: where you upload documents, where you type a regulator question and see the drafted answer with citations, and the review screen where a human approves it. | **TASK-019 → TASK-022** |

**One sentence per person, so everyone can explain their own job in the
demo:** Harieshvaran makes documents searchable. Dharaheshh makes the system
draft grounded, checked answers from that search. Akshay makes it usable and
visible.

### What "Dharaheshh owns main" actually means, day to day

- Everyone else works on their own branch, never commits straight to `main`.
- When Harieshvaran or Akshay finish a task, they push their branch and open
  a Pull Request (PR) — **Dharaheshh reviews and clicks merge.**
- Dharaheshh is also the one who resolves it if two branches conflict on the
  same file.
- This doesn't mean Dharaheshh writes more code than everyone — it means
  Dharaheshh is the last checkpoint before anything becomes "official."

---

## PART 1 — Exact merge order (this is the part you asked for)

Some tasks unblock other people's work. Here's the real dependency chain and
exactly when each person should open a PR and when Dharaheshh should merge
it.

| Order | Who | Finishes | Then merge into `main` | Why — what it unblocks |
|---|---|---|---|---|
| 1 | Everyone | TASK-001 (repo bootstrap) | Merge immediately, together | Nothing to build without this |
| 2 | Dharaheshh | TASK-002 + TASK-003 (DB schema + backend health check) | Merge immediately | Both other people need real tables and a live backend to build against |
| 3 | Akshay | TASK-004 (frontend scaffold) | Merge immediately | — |
| 4 | Harieshvaran | TASK-005 (PDF parser) | **Merge as soon as its test passes** | Nothing downstream yet, but merge early anyway — don't sit on it |
| 5 | Harieshvaran | TASK-006 (chunker) | **Merge as soon as its test passes** | Same |
| 6 | Harieshvaran | TASK-007 (embeddings + evidence rows) | **Merge — this is a big unblock** | This creates the `evidence` table data. Dharaheshh's TASK-013 (citation validator) needs this to exist. Akshay can start real corpus uploads after this too. |
| 6b | Dharaheshh | TASK-011 (requirement extraction) | **Merge whenever ready — doesn't depend on Harieshvaran at all** | Build this in parallel, right from hour 2-4. It only needs a query string, nothing else. |
| 6c | Dharaheshh | TASK-013 (citation validator) | **Merge right after TASK-007 lands** | Only needs the `evidence` table to exist |
| 7 | Harieshvaran | TASK-008 (document upload endpoints) | **Merge — unblocks Akshay** | Akshay's Library page (TASK-019) can now hit the REAL backend instead of fake/mocked data |
| 8 | Akshay | TASK-019 (Library page) | Merge once real backend (step 7) exists — before that, build it against fake JSON data, no need to wait | Upload screen becomes real |
| 9 | Harieshvaran | TASK-009 (hybrid retrieval / search) | **Merge — big unblock for Dharaheshh** | Dharaheshh's TASK-012 (response generation) needs real search results to build the evidence pack it sends to the AI |
| 10 | Dharaheshh | TASK-012 (response generation + citations) | Merge right after step 9 | — |
| 11 | Dharaheshh | TASK-014 (the endpoint that connects query → requirements → search → draft → citations, all together) | Merge once TASK-009, 011, 012, 013 are all in `main` | This is the real "ask a question, get an answer" endpoint |
| 12 | Akshay | TASK-020 (Query Workspace page) | Merge once step 11 exists — build against fake data before that | This is your first real end-to-end demo path working |

### 🚩 HOUR 16 CHECKPOINT — MANDATORY

**Everyone merges whatever they have right now, no matter how unfinished.**
Then all three of you run the whole thing together once: upload → ask a
question → see something come back. This is not optional. If it's broken,
you have 20 hours left to fix it. If you skip this and find out at hour 30,
you don't.

| Order | Who | Finishes | Then merge into `main` | Why |
|---|---|---|---|---|
| 13 | Dharaheshh | TASK-015 (claim vs. evidence check — catches overclaiming) | Merge when ready | — |
| 14 | Dharaheshh | TASK-016 (evidence sufficiency — the "we don't have enough evidence" feature) | Merge when ready | Doesn't depend on TASK-017, can be built in any order with it |
| 15 | Dharaheshh | TASK-017 (contradiction detection) | Merge when ready | This is your #2 killer demo feature — prioritize it if time is tight |
| 16 | *(unassigned — flagging below)* | TASK-018 (approve/reject endpoints) | Needed before Akshay's review screen works for real | See note below |
| 17 | Akshay | TASK-021 (contradiction panel + "not enough evidence" panel) | Merge once TASK-016/017 are in `main` | Your #2 and #3 killer demo moments become visible on screen |
| 18 | Akshay | TASK-022 (review/approve screen + audit trail) | Merge once TASK-018 exists | Human-in-the-loop, the final piece |

**⚠️ Note: TASK-018 (approve/reject endpoints) wasn't assigned to anyone.**
Someone needs to own it — suggest Dharaheshh picks it up right after TASK-017
since it's a small, quick task and he's already deep in that part of the
codebase. Decide this now, not at hour 20.

---

## PART 2 — Example: what this actually looks like in the terminal

Say Harieshvaran just finished TASK-007. Here's exactly what he types:

```bash
# Harieshvaran, on his own machine:
git add .
git commit -m "feat(ingestion): generate embeddings and evidence rows

Refs: TASK-007"
git push -u origin feat/ingestion
```

Then he goes to GitHub, opens a Pull Request from `feat/ingestion` into
`main`, and messages the group: *"TASK-007 done, PR is up, this unblocks
citation validation and corpus uploads."*

Dharaheshh reviews it (does it match what `TASKS.md` asked for? do the tests
actually pass?) and clicks **Merge**.

Then everyone else does:

```bash
git checkout main
git pull
```

...to get Harieshvaran's new code onto their own machine before continuing.

**Do this every single time someone merges something you depend on.** If
Dharaheshh merges TASK-007 and Dharaheshh himself is about to start TASK-013
(which needs it), he doesn't need to `pull` since he already has it locally
— but Akshay and Harieshvaran should still pull if they're about to build on
top of it.

---

## PART 3 — Docker in plain English

### The idea

Our project needs a database (Postgres), a backend (FastAPI), and a frontend
(React) all running at the same time, all talking to each other. Instead of
installing all that stuff directly on your laptop — which gets messy and
behaves differently on everyone's machine — Docker runs each piece inside its
own **sealed little box**. Same box, same behavior, on anyone's computer.

### The four words you need

| Word | What it actually means |
|---|---|
| **Image** | The blueprint for a box (e.g. "a Postgres 16 + pgvector blueprint") |
| **Container** | An actual running box made from that blueprint |
| **`docker-compose.yml`** | A shopping list: "start these 3 boxes together, on this network, so they can talk to each other" |
| **Volume** | A folder that survives even if you turn the box off — this is how our database doesn't forget everything every time we restart |

### The commands you'll actually type (this is basically the whole list)

```bash
docker compose up -d          # turn on ALL the boxes (db, backend, frontend), in the background
docker compose up -d db       # turn on just the database box
docker compose ps             # "what's running right now?"
docker compose logs backend   # "show me what the backend box has been printing" — use this to debug
docker compose logs -f backend # same, but keep watching live (Ctrl+C to stop watching)
docker compose down           # turn everything off
docker compose build backend  # rebuild the backend box (do this after changing requirements.txt or Dockerfile)
docker compose exec backend bash   # "open a terminal INSIDE the running backend box" — useful for debugging
docker compose exec backend pytest -v   # run the backend tests, inside the box
```

### Your actual daily routine

```bash
docker compose up -d       # start of your session
# ...do your work...
docker compose logs -f backend   # if something's broken, watch the logs
docker compose down        # end of your session (optional — you can also just leave it running)
```

### When something's broken

1. `docker compose ps` — is the box even running? If it says "Exited" or
   isn't listed, it crashed.
2. `docker compose logs <service-name>` — read the actual error. 90% of the
   time the answer is right there (usually: wrong env variable, or the
   database wasn't ready yet when the backend tried to connect).
3. `docker compose down && docker compose up -d --build` — nuclear option,
   rebuilds everything fresh. Fixes most "it worked yesterday" problems.

### One thing that trips people up

The database needs a few seconds to actually be ready after `docker compose
up`. If your backend crashes immediately complaining it can't connect to
Postgres, just wait 5 seconds and try again, or check that `docker-compose.yml`
has the `depends_on: db: condition: service_healthy` line — that makes the
backend automatically wait for Postgres to be ready.

---

## PART 4 — Git in plain English

### The idea

Git tracks "save points" of your code over time. Think of it like a video
game save file, except every teammate can create their own save points and
merge them together.

### The five words you need

| Word | What it actually means |
|---|---|
| **Repository (repo)** | The whole project folder, with its save-point history — ours is called **Regulens** |
| **Commit** | One save point — a snapshot of your code plus a note about what changed |
| **Branch** | A parallel timeline — you can make changes here without touching the "real" version until you're ready |
| **Merge** | Combining a branch's changes back into the main timeline |
| **Pull Request (PR)** | "Hey team, here's a branch I finished — can we merge it into main?" (a review step before merging) |

### `main` is sacred, and Dharaheshh owns it

Nobody edits `main` directly — not even Dharaheshh, technically (he still
works on branches for his own tasks). The difference is Dharaheshh is the one
who reviews and clicks the merge button on everyone's PRs, including his own.

### The commands you'll actually type

```bash
# ONE-TIME SETUP (do this once, at the very start)
git clone <the-github-url>       # download the project onto your laptop
cd regulens

# EVERY TIME YOU START NEW WORK
git checkout main                # make sure you're on the main timeline
git pull                         # get the latest changes your teammates made
git checkout -b feat/my-task     # create YOUR OWN branch to work on

# WHILE YOU'RE WORKING (do this often — every 30-60 min, not just at the end)
git add .                        # "stage" all your changed files
git commit -m "feat: what I just did"   # save a point, with a short description

# WHEN YOU'RE DONE (or want to save your progress remotely)
git push -u origin feat/my-task  # upload your branch to GitHub (first time)
git push                         # upload your branch (every time after)

# THEN: go to GitHub.com, open a "Pull Request" from your branch into main
# Dharaheshh reviews it, then clicks "Merge"

# AFTER YOUR BRANCH IS MERGED
git checkout main
git pull                         # get your own merged changes + anyone else's
git branch -d feat/my-task       # delete your old branch, you're done with it
```

### Branch names for this project — use these exact names

```
feat/generation-validation    — Dharaheshh, TASK-011 through TASK-017
feat/ingestion                — Harieshvaran, TASK-005 through TASK-009
feat/frontend                 — Akshay, TASK-019 through TASK-022
```

If a task within your range is big enough to want its own branch (e.g.
Dharaheshh might want `feat/generation-validation` split into smaller
branches per task if it gets unwieldy), that's fine — just keep the naming
consistent, e.g. `feat/task-013-citation-validator`.

### Commit messages — keep them useful, not fancy

```
feat(ingestion): add PDF parsing with page number tracking

Refs: TASK-005
```

Format: `type(area): what happened`, plus a `Refs: TASK-XXX` line so
anyone can trace a commit back to `TASKS.md`. Types: `feat` (new thing),
`fix` (bug fix), `docs` (documentation only), `test` (just tests), `chore`
(setup/config stuff).

### Merge conflicts — don't panic

A conflict just means two people edited the *same lines* of the *same file*.
Git can't guess which version you want, so it asks you.

```bash
git pull   # or merging your branch — this is when a conflict shows up
```

You'll see something like this inside the conflicted file:

```
<<<<<<< HEAD
your version of the code
=======
their version of the code
>>>>>>> feat/their-branch
```

Just manually edit the file to keep whichever version (or a mix) is correct,
delete the `<<<<<<<`, `=======`, `>>>>>>>` lines, then:

```bash
git add .
git commit -m "fix: resolve merge conflict"
```

**How to avoid most conflicts entirely:** you're each working in different
folders (`backend/app/ingestion/` vs `backend/app/generation/` +
`validation/` vs `frontend/`), so you'll rarely touch the same file as
someone else. The one shared risk is `backend/app/models.py` and migration
files — if you're about to edit one of these, give a heads-up in the group
chat first, since Dharaheshh will most often be the one touching these
(they're closest to his tasks).

### If you completely mess something up

```bash
git status                # "what's going on right now?" — always start here
git checkout -- <file>    # undo changes to one file you haven't committed yet
git reset --hard HEAD     # nuke ALL uncommitted changes, go back to last commit (careful — this deletes work)
```

If a bad commit already got merged into `main` and broke things:

```bash
git revert <commit-hash>  # creates a NEW commit that undoes a bad one — safe, doesn't rewrite history
```

Don't use `git reset --hard` on `main` or on commits already pushed — that
rewrites history and will mess up your teammates' copies. `git revert` is
always the safe undo button for shared branches.

---

## PART 5 — The daily loop, start to finish

This is what every single task looks like, every time, for all three of you:

```bash
git checkout main
git pull
git checkout -b feat/my-next-task

# ...write code, run Antigravity, whatever...

docker compose up -d
docker compose exec backend pytest -v    # make sure tests pass

git add .
git commit -m "feat(scope): what you did

Refs: TASK-XXX"
git push -u origin feat/my-next-task

# open a Pull Request on GitHub — Dharaheshh reviews and merges

git checkout main
git pull
git branch -d feat/my-next-task
```

Repeat, forever, for 36 hours.

---

## Extra thing worth adding: a quick daily sync

With only 3 people and 36 hours, a 2-minute voice-note or message every few
hours ("just merged TASK-007, this unblocks citation validation") saves way
more time than it costs. You don't need a formal standup — just say out loud
in the group chat every time you merge something that unblocks someone else,
since that's exactly the moment the other person needs to `git pull`.

---

## Quick reference card (screenshot this)

**Docker:**
```
docker compose up -d          start everything
docker compose ps             is it running?
docker compose logs -f X      why is X broken?
docker compose down           stop everything
```

**Git:**
```
git checkout -b feat/x        start new work
git add . && git commit -m "" save your progress
git push                      upload it
git pull                      download teammates' work
```

**Who owns what:**
```
Dharaheshh    — main branch + TASK-011→017 (generation & validation)
Harieshvaran  — TASK-005→009 (ingestion & retrieval)
Akshay        — TASK-019→022 (frontend)
Unassigned    — TASK-018 (approve/reject endpoints) — decide who takes this NOW
```
