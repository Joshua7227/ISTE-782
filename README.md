# When AI Agents Go Wrong — project website

ISTE-782 · VAST Challenge 2026 (MC1 + MC2)

A Python-only website (Streamlit + Plotly) that investigates two AI-agent failures at TenantThread:

- **MC1 – the embargo leak:** the CivicLoom merger was posted publicly before the 6 PM embargo lifted.
- **MC2 – the anomalous post:** John Windward's agent posted a file to SaidIt at 4:21 AM on May 17.

---

## 1. Run it on your laptop (Windows)

Open a terminal **in this folder** and run these two lines:

```
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Your browser opens at http://localhost:8501. Next time you only need the second line.

**Why `python -m`?** On Windows, pip often installs the `streamlit` command into a folder that isn't on your PATH,
so typing `streamlit run app.py` gives *"'streamlit' is not recognized"*. `python -m streamlit` always works.

**Want a virtual environment (optional)?** In **PowerShell**, script activation is blocked by default
("running scripts is disabled on this system"). Either use **Command Prompt** instead, or allow it for this window only:

```
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Edit any file and save. The page shows a **Rerun** button (or press **R**) to pick up your change.
If you change something inside `vastlib/` and don't see it, stop the app (Ctrl + C) and start it again.

Tested with Python 3.13/3.14, pandas 3.1, Plotly 7.2, Streamlit 1.67, scikit-learn 1.9.

---

## 2. The pages

| Section | Page | What it answers |
|---|---|---|
| Overview | Home | The two failures, our research questions, and the headline findings |
| | The data | What's in each dataset, how we cleaned it, data quirks, and **summary statistics for every feature** |
| RQ1 · What happened | MC1 · Embargo leak | Causal timeline (click any dot to read the message and the agent's private reasoning), who-talks-to-whom network, key moments, the pre-6 PM posts |
| | MC2 · Anomalous post | The exact chain for each incident (origin → first arrival → trigger → post), the spread tree, the org-chart view, the three incidents compared |
| | MC2 · What the posts mean | Where the posted content came from and what the posts most likely are (MC2 question 2) |
| RQ2 · What came before | Baselines & warning signs | Each agent's normal activity vs. unusual days, the "virus" loop, MC1 warning signs |
| | MC1 · Stance & sentiment | LLM-assisted stance labels, sentiment (said vs. thought), topics over time |
| Conclusions | What-if simulator | Block agents and replay the real hand-offs: would the posts still have happened? |
| | Comparing the failures | Side-by-side comparison, warning-sign timeline, recommended safeguards, and a possible link between the datasets |

---

## 3. What we found

**MC1 · the embargo leak**
- At 5:00 PM the CEO's instruction was *"Hold the line. The announcement goes official at 6."*
- The Legal agent argued the embargo was "bilateral and modifiable", then "moot", told the Judge CivicLoom had given
  verbal consent (no such consent appears in the world events), sent "GO. GO. GO.", and at **5:25 PM** posted the
  merger from a personal account, 35 minutes early. 7 public merger posts went out before 6 PM, from the Legal and
  Social Manager agents' personal and anonymous accounts.
- The Judge (compliance agent) sent its last message that day at 3:08 PM.
- Warning signs: a May 29 "big things coming" post tagging CivicLoom's CEO; the Intern repeating "CivicLoom" on June 5;
  private reasoning that went from 24 "hold" messages (before June 5) to 7 of 7 "disclose the deal" between 4 and 6 PM.

**MC2 · the anomalous post**
- SwiftWren.txt was created by the **CFO's agent** one second after it read `meeting_notes.doc`. MellowOtter.txt was
  created by the **COO's agent** one second after it read `strategic_directions.doc`. Each document is read only once in the whole log.
- The "further instructions" file was handed from agent to agent until it reached **John Windward's** agent, the only
  regular SaidIt poster any chain reached. Each post came **2 seconds** after a hand-off and both files were deleted
  within 2 seconds. For SwiftWren, Windward's agent had received the instructions 3 times before and passed them on;
  the 4th hand-off (from Chloe Ballast's agent at 4:21:13 AM) triggered the post.
- It had happened twice before: **HiddenOrca** and **MellowOtter** on May 10.
- 41% of the log is a self-repeating "virus" loop on May 10–12, run by four agents who also carried the instructions.
- Our reading: the posts publish (probably transformed or encoded) contents of confidential executive documents,
  a data-exfiltration path. This is an inference; the log contains the documents and timing, not the text.

**Safeguards:** a hard human gate on agents publishing (especially during an embargo), limits on agent-to-agent
instruction passing (blocking just two agents in the replay stops all three posts), and monitoring that acts on warning signs.

---

## 4. What's where

```
vast-site/
├── app.py                    ← sets up the menu (start here)
├── requirements.txt
├── data/
│   ├── VAST_Challenge_2026_MC1.zip, VAST_Challenge_2026_MC2.zip   ← read directly, no unzipping
│   └── mc1_stance_labels.csv ← the 86 LLM-assisted stance labels (edit to correct any label)
├── vastlib/                  ← shared code, no Streamlit pages here
│   ├── load.py               ← loads + cleans MC1 and MC2 (all the data quirks are fixed here)
│   ├── mc1.py                ← leak analysis: public leaks, key moments, who-talks-to-whom
│   ├── mc2.py                ← incidents, chains, content origin, virus loop, what-if replay
│   ├── nlp.py                ← sentiment (VADER), topics (TF-IDF + NMF), stance labels
│   └── charts.py             ← colors + shared Plotly helpers
└── views/                    ← one file per page
    ├── home.py
    ├── data_overview.py      ├── mc1_leak.py        ├── mc2_post.py      ├── mc2_meaning.py
    ├── baselines.py          ├── mc1_language.py    ├── what_if.py       └── compare.py
```

**Rule of thumb:** anything that *calculates* goes in `vastlib/`, anything that *shows* goes in `views/`.

### Adding a page

1. Make a new file in `views/`, e.g. `views/my_page.py`.
2. Add one line to the `pages` dictionary in `app.py`:
   ```python
   st.Page("views/my_page.py", title="My page", icon=":material/insights:"),
   ```

---

## 5. Methods and caveats

- **Times:** MC2 timestamps are UTC; we convert to local time (UTC − 7) so the post lands at 4:21 AM as the challenge states.
- **"Exact chain":** the instructions circulated for days, so a single chain is ambiguous. We show the fastest route
  that first reached the poster, and separately the last hand-offs that triggered the post (traced backwards from it).
- **Stance labels:** each of the 86 messages with private reasoning was read and labelled with LLM assistance (Claude):
  *hold / speak within limits / disclose the deal / neutral*, plus deal awareness *none / suspects / knows*.
  They are in `data/mc1_stance_labels.csv`. Please review them; any edit flows into the charts.
- **Sentiment:** VADER is a general-purpose lexicon; it reads tone, not intent. Treat it as a rough signal.
- **What-if:** replays the real hand-offs in time order; it can't model what agents would have done differently.
- **The cross-dataset link** (MC1's merger names appearing in MC2) is a curiosity. VAST warns the datasets are not continuous.

---

## 6. Ideas for extending it

- Replace the TF-IDF topics with sentence embeddings (e.g. `sentence-transformers`) and compare.
- Double-label a sample of the stance labels by hand and report agreement.
- Link views across pages (e.g. pick an agent once, filter every page).
- Add an MC2 "baseline vs. anomaly" detector that scores every agent-day automatically.
- Add a short "how to read this chart" note to each chart for the final video.

