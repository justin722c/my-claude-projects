# Realtor AI Guide

- `00-master-prompt.md` — the prompt that generates the product
- `01-the-15-minute-agent.md` — the guide (output of that prompt)
- `02-sales-payment-delivery.md` — pricing, sales copy, how to get paid and deliver
- `03-marketing-plan.md` — 60-day step-by-step launch and marketing plan
- `output/` — finished branded PDFs (the guide to sell; the internal launch playbook)
- `assets/` — Team Smith Homes logo (extracted from the hat photo; swap in your vector/PNG logo for best quality) and fonts
- `build/build.py` — regenerates the PDFs: `python3 build/build.py` (needs `pip install markdown pypdf` and Chromium)

**Source note:** the Soulprint tool and the Residual Agent guide (getresidualagent.com/claude-guide, by Brian Force) were incorporated from user-provided screenshots because the sandbox blocked both sites; the Lighthaus PDF was read from Google Drive. Prompts are rewritten, not copied. Screenshots of the Residual Agent guide ended at the first-week plan, so any content below that was not seen.
