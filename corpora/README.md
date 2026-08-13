# Corpus folders

Place one `.txt` document per file in each folder.

- `pre_ai_human/` — human writing from before widespread generative-AI writing adoption.
- `contemporary_human/` — recent human writing with credible provenance and minimal/disclosed AI assistance.
- `ai_assisted/` — AI-generated or materially AI-assisted writing with known provenance where possible.

For real experiments, add a `metadata.csv` at the corpus root with columns such as:

```csv
file,corpus,date,genre,source,provenance,model,prompt_family
```

Do not commit copyrighted corpora to a public repository unless redistribution is permitted. Prefer scripts or documented instructions that reconstruct public datasets locally.
