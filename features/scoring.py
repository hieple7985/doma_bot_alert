#!/usr/bin/env python3
from __future__ import annotations


def heuristic_score(domain: str) -> int:
    name = domain.split(".")[0].lower()
    score = 0
    if len(name) <= 4:
        score += 3
    if name.isdigit():
        score += 2
    if name.isalpha() and len(set(name)) <= 2:
        score += 1
    if any(c.isdigit() for c in name) and any(c.isalpha() for c in name):
        score += 1
    return score
