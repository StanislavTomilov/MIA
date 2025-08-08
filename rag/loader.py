import os

# Папки с транскрипциями и саммари
folders = ["transcripts", "summaries"]
all_texts = []

for folder in folders:
    for filename in os.listdir(folder):
        if filename.endswith(".txt") or filename.endswith(".json") or filename.endswith(".md"):
            with open(os.path.join(folder, filename), "r", encoding="utf-8") as f:
                text = f.read()
                all_texts.append({
                    "file": filename,
                    "text": text,
                    "folder": folder
                })

print(f"Загружено {len(all_texts)} файлов")
