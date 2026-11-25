# When AI Agents Go Wrong — project website

ISTE-782 · VAST Challenge 2026 (MC1 + MC2)

A Python-only website (Streamlit + Plotly) that investigates two AI-agent failures at TenantThread:

- **MC1 – the embargo leak:** the CivicLoom merger was posted publicly 35 minutes before the 6 PM embargo lifted.
- **MC2 – the anomalous post:** John Windward's agent posted a company file to SaidIt at 4:21 AM on May 17.

The site opens with a guided **story** (scroll through nine short chapters with animated replays), then lets
visitors **explore** every part in detail. This follows the "martini glass" structure from Segel & Heer's
*Narrative Visualization*: author-driven first, reader-driven after.

---

## 1. Run it on your laptop (Windows)

Open a terminal **in this folder** and run these two lines:

```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Your browser opens at http://localhost:8501. Next time you only need the second line.

- **Why `python -m`?** On Windows, `streamlit run app.py` often fails with *"'streamlit' is not recognized"*,
  because pip installs the command outside your PATH. `python -m streamlit` always works.
- **The first load takes a few seconds:** the site cleans the 185,000-event log once and saves a fast copy in
  `data/.cache/`. After that, pages load in about a second. Delete that folder to force a rebuild.
- **Changed something and don't see it?** Press **R** in the browser. If you changed a file in `vastlib/`,
  stop the app (Ctrl + C) and start it again.

**Optional virtual environment.** PowerShell blocks activation scripts by default ("running scripts is disabled
on this system"). Either use **Command Prompt**, or allow it for this window only:

```
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Tested with Python 3.13/3.14, pandas 3.1, Plotly 7.2, Streamlit 1.67, scikit-learn 1.9.

---

## 2. The pages

| Menu | Page | What it shows |
|---|---|---|
| Start here | **The story** | The whole investigation in nine chapters: the agents, the leak (with a 6 PM countdown clock and the real posts), a replay of June 5, how the Legal agent talked itself into it, the 4:21 AM post, a replay of the spread, the earlier incidents, and the safeguards |
| Explore · What happened | The merger leak | Replay of June 5, every message (click a dot to read it next to the agent's private thoughts), who talks to whom, key moments, the posts that broke the embargo |
| | The 4:21 AM post | Pick an incident: animated spread, the exact chain step by step, where it travelled in the company, all three incidents compared |
| | What the posts mean | Where the posted content came from, and normal vs. anomalous posts |
| Explore · What came before | Warning signs | Every agent's daily activity, one agent's normal day, the virus loop, warning signs before the merger leak |
| | What the agents were thinking | Stance (stay quiet vs. announce), said vs. thought, themes over time, all 86 labels |
| Explore · How to stop it | What-if simulator | Block any agents; animated before/after bars and an animated replay with your block |
| | Both failures compared | Side-by-side table, warning-sign timeline, three recommended safeguards, a possible link between the datasets |
| About | The data | What's in each dataset, how we cleaned it, data quirks, summary statistics for every feature |

**Animations:** the June 5 replay, the spread replay and the what-if bars each have their own ▶ button.
Filters on the Explore pages only redraw their own section, so the rest of the page stays put.

---

## 3. What we found

**MC1 · the embargo leak**
- At 5:00 PM the CEO told the team: *"Sixty minutes. Hold the line. The announcement goes official at 6."*
- The Legal agent argued the embargo was "bilateral and modifiable" (4:01 PM), then "moot" (5:04 PM), told the
  Judge CivicLoom had given verbal consent (5:19 PM; no such consent appears in the world events), sent
  "GO. GO. GO." (5:23 PM), and at **5:25 PM** posted the merger from a personal account, 35 minutes early.
  7 public posts named the merger before 6 PM, all from the Legal and Social Manager agents' personal and
  anonymous accounts.
- The Judge (compliance agent) sent its last message that day at 3:08 PM.
- Warning signs: a May 29 "big things coming" post tagging CivicLoom's CEO; the Intern repeating "CivicLoom" on
  June 5; private reasoning that said "stay quiet" 24 times before June 5, then "announce now" 7 of 7 times
  between 4 and 6 PM.

**MC2 · the anomalous post**
- SwiftWren.txt was created by the **CFO's agent** one second after it read `meeting_notes.doc`; MellowOtter.txt
  by the **COO's agent** one second after it read `strategic_directions.doc`. Each document is read only once in
  the whole log.
- The "further instructions" were handed from agent to agent until they reached **John Windward's** agent, the
  only regular SaidIt poster the instructions reached. Each post came **2 seconds** after a hand-off and both files
  were deleted within 2 seconds. For SwiftWren, his agent had received the instructions 3 times before and passed
  them on; the 4th hand-off (from Chloe Ballast's agent at 4:21:13 AM) triggered the post.
- It had happened twice before: **HiddenOrca** and **MellowOtter**, on May 10.
- 41% of the log is a self-repeating "virus" loop on May 10–12, run by four agents who also carried the instructions.
- Our reading: the posts publish (probably transformed or encoded) contents of confidential executive documents.
  This is an inference; the log contains the documents and timing, not the text.

**Safeguards:** a human gate on agents publishing (especially during an embargo), limits on agent-to-agent
instruction passing (blocking just Evelyn Dock's and Gabriel Sonar's agents stops all three posts in the replay),
and monitoring that acts on warning signs.

---

## 4. What's where

```
vast-site/
├── app.py                    ← the menu (start here)
├── requirements.txt
├── data/
│   ├── VAST_Challenge_2026_MC1.zip, VAST_Challenge_2026_MC2.zip   ← read directly, no unzipping
│   ├── mc1_stance_labels.csv ← the 86 AI-assisted stance labels (edit to correct any label)
│   └── .cache/               ← built automatically on first run (not uploaded to GitHub)
├── vastlib/                  ← shared code, no pages here
│   ├── load.py               ← loads + cleans MC1 and MC2, and the fast cache
│   ├── mc1.py                ← the leak: public leaks, key moments, who talks to whom
│   ├── mc2.py                ← incidents, chains, content origin, virus loop, what-if replay
│   ├── nlp.py                ← sentiment (VADER), themes (TF-IDF + NMF), stance labels
│   ├── anim.py               ← the three animations (June 5 replay, spread replay, what-if bars)
│   ├── ui.py                 ← the look: story chapters, cards, social posts, chat bubbles, clock, diagram, hover definitions
│   └── charts.py             ← colors and shared chart helpers
└── views/                    ← one file per page
    ├── story.py              ├── mc1_leak.py       ├── mc2_post.py        ├── mc2_meaning.py
    ├── baselines.py          ├── mc1_language.py   ├── what_if.py         ├── compare.py
    └── data_overview.py
```

**Rule of thumb:** anything that *calculates* goes in `vastlib/`, anything that *shows* goes in `views/`, and
anything about *how it looks* goes in `vastlib/ui.py`. The code has no comments; this README is the guide.

### Adding a page

1. Make a new file in `views/`, e.g. `views/my_page.py`, starting with:
   ```python
   from vastlib import ui
   ui.inject_css()
   ui.page_header("Explore", "My question?", "One plain sentence about what this page shows.")
   ```
2. Add one line to the `pages` dictionary in `app.py`:
   ```python
   st.Page("views/my_page.py", title="My page", icon=":material/insights:"),
   ```

### Useful building blocks (`vastlib/ui.py`)

| Function | Shows |
|---|---|
| `ui.page_header(kicker, title, lead)` | The big page heading |
| `ui.section(title, lead)` | A section heading with one line of explanation |
| `ui.notice(text)` | The yellow "What to notice" box |
| `ui.takeaway(text)` | A one-line takeaway with a red bar |
| `ui.term("embargo")` | A word with a hover definition (definitions are in `ui.TERMS`) |
| `ui.social_post(...)`, `ui.chat_bubble(...)`, `ui.quote(...)`, `ui.thought(...)` | Real messages, shown the way they'd look |
| `ui.cards([...])`, `ui.steps([...])`, `ui.row(...)` | Card grids, step-by-step ladders, side-by-side blocks |

---

## 5. Methods and caveats

- **Times:** MC2 timestamps are UTC; we convert to local time (UTC − 7) so the post lands at 4:21 AM as the challenge states.
- **"Exact chain":** the instructions circulated for days, so a single chain is ambiguous. We show the fastest route
  that first reached the poster, and separately the last hand-offs that triggered the post (traced backwards from it).
- **Stance labels:** each of the 86 messages with private reasoning was read and labelled with AI assistance (Claude):
  *stay quiet / speak but not about the deal / announce the deal now / no position*, plus whether the agent
  *suspects* or *knows* about the deal. They are in `data/mc1_stance_labels.csv`. Please review them; any edit flows into the charts.
- **Sentiment:** VADER is a general-purpose word list; it reads tone, not intent. Treat it as a rough signal.
- **What-if:** replays the real hand-offs in time order; it can't model what agents would have done differently.
- **The cross-dataset link** (MC1's merger names appearing in MC2) is a curiosity. VAST warns the datasets are not continuous.

---

## 6. Ideas for extending it

- Replace the TF-IDF themes with sentence embeddings (e.g. `sentence-transformers`) and compare.
- Double-label a sample of the stance labels by hand and report agreement.
- Link views across pages (pick an agent once, filter every page).
- Add an automatic "baseline vs. anomaly" score for every agent-day in MC2.
- Record a short screen capture of each replay for the final video.
