from ingest import search

for r in search(input("اكتبي سؤالك: ")):
    print(f"[{r['source']} - ص{r['page']}] {r['text'][:200]}\n")
