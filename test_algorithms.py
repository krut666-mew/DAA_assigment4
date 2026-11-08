"""Additional deterministic and randomized checks for the Python solution."""
import itertools
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "Python" / "source"))
import algorithms


def is_subsequence(candidate, source):
    it = iter(source)
    return all(any(ch == item for item in it) for ch in candidate)


class Assignment4Tests(unittest.TestCase):
    def test_lcs_random(self):
        rng = random.Random(4104)
        for _ in range(100):
            a = "".join(rng.choice("abc") for _ in range(rng.randrange(9)))
            b = "".join(rng.choice("abc") for _ in range(rng.randrange(9)))
            result = algorithms.lcs({"a": a, "b": b})
            self.assertEqual(result["length"], len(result["sequence"]))
            self.assertTrue(is_subsequence(result["sequence"], a))
            self.assertTrue(is_subsequence(result["sequence"], b))
            brute = max((len(x) for r in range(min(len(a), len(b)) + 1)
                         for x in map("".join, itertools.combinations(a, r))
                         if is_subsequence(x, b)), default=0)
            self.assertEqual(result["length"], brute)

    def test_merge_plan_random(self):
        rng = random.Random(4204)
        for n in range(8):
            for _ in range(15):
                sizes = [rng.randrange(8) for _ in range(n)]
                result = algorithms.merge({"sizes": sizes})
                blocks = [(i, i, sizes[i]) for i in range(n)]
                total = 0
                for left, split, right in result["plan"]:
                    idx = next(i for i, block in enumerate(blocks)
                              if block[0] == left and block[1] == split)
                    self.assertEqual(blocks[idx + 1][:2], (split + 1, right))
                    cost = blocks[idx][2] + blocks[idx + 1][2]
                    total += cost
                    blocks[idx:idx + 2] = [(left, right, cost)]
                self.assertEqual(len(blocks), min(n, 1))
                self.assertEqual(total, result["cost"])

    def test_tree_against_subsets(self):
        rng = random.Random(4304)
        for n in range(1, 11):
            for _ in range(25):
                edges = [[v, rng.randrange(v)] for v in range(1, n)]
                weights = [rng.randrange(-5, 10) for _ in range(n)]
                result = algorithms.tree({"n": n, "weights": weights, "edges": edges})
                edge_set = {tuple(sorted(edge)) for edge in edges}
                best = 0
                for mask in range(1 << n):
                    if any((u, v) in edge_set for u in range(n) for v in range(u + 1, n)
                           if mask >> u & 1 and mask >> v & 1):
                        continue
                    best = max(best, sum(weights[i] for i in range(n) if mask >> i & 1))
                selected = result["selected"]
                self.assertEqual(result["weight"], best)
                self.assertEqual(len(selected), len(set(selected)))
                self.assertEqual(sum(weights[i] for i in selected), best)
                self.assertFalse(any(u in selected and v in selected for u, v in edges))

    def test_searches_random(self):
        rng = random.Random(4404)
        for _ in range(250):
            text = "".join(rng.choice("abca ") for _ in range(rng.randrange(25)))
            pattern = "".join(rng.choice("abca ") for _ in range(rng.randrange(9)))
            expected = [i for i in range(len(text) + 1) if text.startswith(pattern, i)]
            for function in (algorithms.naive, algorithms.kmp, algorithms.rk):
                self.assertEqual(function({"text": text, "pattern": pattern})["positions"], expected)

    def test_suffix_random(self):
        rng = random.Random(4504)
        for _ in range(250):
            text = "".join(rng.choice("abcd") for _ in range(rng.randrange(30)))
            result = algorithms.suffix({"text": text})
            expected_sa = sorted(range(len(text)), key=lambda i: text[i:])
            self.assertEqual(result["sa"], expected_sa)
            expected_lcp = [0]
            for i in range(1, len(expected_sa)):
                a, b, h = expected_sa[i - 1], expected_sa[i], 0
                while a + h < len(text) and b + h < len(text) and text[a + h] == text[b + h]:
                    h += 1
                expected_lcp.append(h)
            self.assertEqual(result["lcp"], expected_lcp if text else [])
            repeated = result["repeated"]
            self.assertEqual(len(repeated), max(expected_lcp, default=0))
            if repeated:
                starts = [i for i in range(len(text)) if text.startswith(repeated, i)]
                self.assertGreaterEqual(len(starts), 2)

    def test_aho_random(self):
        rng = random.Random(4604)
        for _ in range(100):
            patterns = ["".join(rng.choice("abc") for _ in range(rng.randrange(1, 5)))
                        for _ in range(rng.randrange(8))]
            texts = ["".join(rng.choice("abc") for _ in range(rng.randrange(15)))
                     for _ in range(rng.randrange(5))]
            actual = algorithms.aho({"patterns": patterns, "texts": texts})["counts"]
            expected = [[sum(text.startswith(p, i) for i in range(len(text) - len(p) + 1))
                         for p in patterns] for text in texts]
            self.assertEqual(actual, expected)

    def test_deep_tree_no_recursion(self):
        n = 100_000
        result = algorithms.tree({"n": n, "weights": [1] * n,
                                  "edges": [[i - 1, i] for i in range(1, n)]})
        self.assertEqual(result["weight"], (n + 1) // 2)
        self.assertEqual(len(result["selected"]), (n + 1) // 2)


if __name__ == "__main__":
    unittest.main()
