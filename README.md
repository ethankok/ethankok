# Hellooo, I'm Ethan Kok! 👋

Year 2 **Data Science & AI** undergraduate at **Nanyang Technological University (NTU), Singapore**. 

I build ML systems and test whether they hold up outside the lab: agents, evaluation, adversarial robustness and inference efficiency on constrained hardware.

- 🔬 **Now:** Undergraduate researcher (URECA, NTU School of EEE) profiling Vision-Language-Action model inference on Jetson-class edge GPUs: per-layer latency, memory footprint and KV-cache growth with PyTorch hooks and NVTX.
- 🏛️ Academic Development Policy Executive, 36th NTU Students' Union.
- 📫 [LinkedIn](https://www.linkedin.com/in/ethankoksj) · ekok003@e.ntu.edu.sg

## Selected work

| Project | What I did | Stack |
|---|---|---|
| [**Synthetic Human Agent — NTU × ST Engineering Hackathon 2026**](https://github.com/aniketmajee7-pixel/NTUxSTEng_Hackathon) | 🏆 **Champion out of 30 teams.** A Python agent that does 15 minutes of unattended office work on an air-gapped Windows 11 VM (Chrome, OpenOffice Calc, Notepad) and passes as a person in Sysmon and process logs. Minimum-jerk, Fitts'-law pointer motion and lognormal typing pauses checked against a 136M-keystroke study; reads Calc's grid from pixels because it exposes nothing to UI Automation. The final run finished in 14:15 at 0.11% CPU and wrote no files of its own. | Python · PyAutoGUI · pywinauto · pywin32 |
| [**TIL-AI 2026 — DSTA BrainHack**](https://github.com/ethankok/til-ai-2026-melanie-minions) | Top 10 Semifinalists out of over 80 participating teams. Technical lead of 5; won both live hardware matches. Built a Dijkstra + PPO exploration agent with CEM-tuned gating, and used HotFlip to find a 16-token adversarial trigger against the white-box answer grader, lifting NLP accuracy from 0.683 to 0.951 (with organiser approval). | Python · PyTorch · PPO · YOLO11 · Docker |
| [**Urban parking demand analysis**](https://github.com/ethankok/sg-carpark-demand) (NTU SC3021) | 7.8M HDB carpark and weather records from 4 Data.gov.sg APIs. k-Means found 4 carpark archetypes and a Simpson's Paradox in the weather correlations; a logistic-regression early-warning model caught 75% of 90%+ occupancy hours. | Pandas · scikit-learn |
| [**Calorpie bot**](https://github.com/ethankok/calorpie-bot) | Telegram calorie tracker with daily users: send a photo, text or voice note and Gemini returns a schema-checked estimate. Designed from the research: LLM photo estimates are off by about 20% per meal, so the card shows one number, is easy to correct, and asks a question only when one detail matters. On chain and plain foods with published values, the eval averages about 4% error. Runs in Docker on an Oracle Always Free VM, tested end to end against a fake Telegram API. | Python · Gemini API · python-telegram-bot · SQLite · Docker |

Smaller builds: [Church Bench](https://github.com/ethankok/church-bench) and [Cute Cat Replacer](https://github.com/ethankok/cute-cat-replacer), two Chrome MV3 extensions.

## Tools

**Languages:** Python, Java, JavaScript, SQL
**ML & data:** PyTorch, scikit-learn, Ultralytics, Hugging Face, Pandas, NumPy, statsmodels
**Systems:** Git, Docker, FastAPI, React, pytest, NVTX
