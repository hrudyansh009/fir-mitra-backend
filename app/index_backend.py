import json
from pathlib import Path


class SimpleIndexBackend:

    def __init__(self, path):
        self.docs = []

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                self.docs.append(json.loads(line))

    def search(self, query, k=7, filters=None):

        query = query.lower()
        results = []

        for doc in self.docs:

            text = doc["text"].lower()

            score = 0

            for word in query.split():
                if word in text:
                    score += 1

            if score > 0:
                results.append((score, doc))

        results.sort(reverse=True, key=lambda x: x[0])

        return results[:k]