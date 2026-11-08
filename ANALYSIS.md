# Assignment 4 — analysis

## Environment and commands

- Selected language: Python.
- Runtime used for the recorded checks: Python 3.13.5 on Linux 6.18.57 x86_64, AMD EPYC 9V74 virtual CPU, approximately 5.8 GiB RAM visible to the container. This is the execution environment used for these measurements, not a claim about the student's personal computer.
- The program uses only the Python standard library.
- Configure the submission: `submission.json` contains `{"language": "Python"}`.
- Startup/transport check: `python tools/run.py --setup`.
- Full public suite: `python tools/run.py --check`.
- Additional student tests: `python -m unittest discover -s tests/student -v`.
- Run one supplied JSONL example: `python tools/run.py --input examples/lcs.jsonl` (replace `lcs` with `merge`, `tree`, `naive`, `kmp`, `rk`, `suffix` or `aho`).
- Run a custom JSONL file: `python tools/run.py --input path/to/requests.jsonl`.

The launcher reads one JSON object per input line and writes one compact JSON result per line. Debug output is not written to standard output. The implementation resets all per-request state by constructing data structures inside each command call.

## Algorithm explanations

### 1. `lcs` — longest common subsequence

**State and indices.** `dp[i][j]` is the length of a longest common subsequence of the prefixes `a[0:i]` and `b[0:j]`. Both indices are prefix lengths, so row zero and column zero represent an empty prefix.

**Transition and order.** If `a[i-1] == b[j-1]`, the two final characters can be appended to an LCS of the shorter prefixes: `dp[i][j] = dp[i-1][j-1] + 1`. Otherwise, an optimal subsequence must omit at least one of the two final characters, so `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`. Rows and columns are filled increasingly; every dependency is in the previous row or an earlier cell in the current row. The zero row and column are base cases.

**Correctness and reconstruction.** The transition considers the optimal possibilities for the two final characters, so induction over increasing prefix lengths proves every table cell optimal. Reconstruction starts at `(len(a), len(b))`. Equal final characters are appended and both indices decrease. On a mismatch, it moves to a neighbor with the same optimal DP value. Reversing the collected characters restores their original order. A tie may choose either neighbor; both preserve an optimal length.

**Complexity.** For lengths `n` and `m`, time and auxiliary memory are `O((n+1)(m+1))`; output uses `O(L)` for the returned subsequence. The implementation handles either empty string before allocating the table.

**Boundary test.** `a=""`, `b="abc"` must return length zero and an empty sequence. This catches incorrect initialization or reconstruction that indexes character `-1`.

### 2. `merge` — ordered adjacent-block merging

**State and indices.** `dp[l][r]` is the minimum total cost to merge the original consecutive blocks from index `l` through `r` into one block. `split[l][r]` stores the final split point `k`. Prefix sums give the total size of an interval in constant time.

**Transition and order.** A final merge must combine `[l,k]` and `[k+1,r]`, for some `l <= k < r`. Therefore `dp[l][r] = min(dp[l][k] + dp[k+1][r] + sum(l..r))`. A single block costs zero. Intervals are processed by increasing length, so both smaller child intervals are already solved.

**Correctness and reconstruction.** Every valid merge plan has a final merge split at one such `k`; before that final merge, its two sides must each have been merged optimally, otherwise replacing a non-optimal side would improve the complete plan. Taking the minimum over all possible final splits is therefore optimal. Reconstruction uses an explicit stack in postorder: first emit the left and right subplans, then `[l,k,r]`. Thus every plan command merges two currently adjacent intervals, and child merges appear before their parent merge.

**Complexity.** Prefix sums take `O(n)`. The interval DP tries `O(n)` splits for each of `O(n^2)` intervals, giving `O(n^3)` time and `O(n^2)` auxiliary memory. Reconstruction is `O(n)` because it emits exactly `n-1` merges. For zero or one block, the result is immediately cost zero and an empty plan.

**Boundary test.** `[0,0,0]` has total cost zero but still requires two adjacent merges. This catches implementations that confuse zero cost with no work, or that merge non-adjacent blocks.

### 3. `tree` — maximum-weight independent set on a tree

**State and indices.** The tree is rooted at vertex zero. `take[u]` is the best weight in the subtree of `u` when `u` is selected; `skip[u]` is the best weight when `u` is not selected. `parent[u]` records the rooted parent. The empty selected set is allowed.

**Transition and order.** `take[u] = weights[u] + sum(skip[v])` over children `v`, because selecting `u` prohibits selecting any child. `skip[u] = sum(max(take[v], skip[v]))`, because each child may make its own best choice. An iterative traversal records parent-before-child order; processing its reverse gives postorder, so every child's DP values are ready before its parent. Iteration avoids Python recursion-depth failure on a long chain.

**Correctness and reconstruction.** In a tree, child subtrees are disjoint and have no edges between them. Conditioning on whether `u` is selected separates the subproblems exactly as the two recurrences state. Induction from leaves proves the DP values optimal. Reconstruction starts with the better root state. If a parent is selected, each child must be skipped; otherwise each child chooses its better state. Ties choose skip, which is still optimal. Negative weights never force a selection because skip permits the empty set.

**Complexity.** Building adjacency, traversal, DP and reconstruction each take `O(n)` time and `O(n)` auxiliary memory. The empty tree takes `O(1)`.

**Boundary test.** A 100,000-vertex chain with all weights equal to one must return weight 50,000 and 50,000 non-adjacent vertices. This catches recursive DFS/DP implementations that exceed the recursion limit.

### 4. `naive` — direct exact string search

**Invariant and indices.** For each candidate start `s` from zero through `n-m`, compare pattern index `j` with text index `s+j`. At the beginning of each candidate, `j=0`; after `j` successful comparisons, the first `j` pattern characters match that window.

**Update and correctness.** The inner loop advances while characters are equal. A candidate is reported only if all `m` characters match. Every possible legal start is visited in increasing order, so all occurrences, including overlaps, are returned exactly once and in sorted order.

**Boundaries.** If `m=0`, every boundary `0..n` is a match. If `m>n`, there is no legal start and the result is empty.

**Complexity.** Time is `O(n*m+n+1)` including output; auxiliary working memory is `O(1)` beyond the `O(z+1)` positions output.

**Boundary test.** Text `"aaaa"`, pattern `"aa"` must return `[0,1,2]`. This catches skipping overlapping occurrences.

### 5. `kmp` — Knuth–Morris–Pratt search

**State and indices.** The prefix function `pi[i]` is the length of the longest proper prefix of `pattern[0:i+1]` that is also its suffix. During text scanning, `j` is the number of pattern characters currently matched.

**Update and order.** The prefix function is built from left to right. On a mismatch, KMP repeatedly sets `j = pi[j-1]`, retaining the longest suffix that could still be a prefix; it does not move the text index backwards. On a match, `j` increases. When `j=m`, a match starts at `i-m+1`, and `j` falls back to `pi[j-1]` so overlapping matches remain possible.

**Correctness.** The prefix function records every possible proper border length needed after a mismatch. Any longer shift would discard a valid prefix/suffix alignment, while a shorter fallback is unnecessary until the longest border has been tested. Thus no possible match is skipped. A full match is reported at its exact start and the same border fallback preserves subsequent overlaps.

**Complexity.** Prefix construction is `O(m)` and scanning is `O(n)` amortized because each increase of `j` is paid for by a later decrease. Total time is `O(n+m+z+1)`, auxiliary memory `O(m+1)`, plus `O(z+1)` output memory.

**Boundary test.** Text `"abababa"`, pattern `"aba"` must return `[0,2,4]`. This catches resetting `j` to zero after a full match and losing overlaps.

### 6. `rk` — Rabin–Karp exact search

**Hash definition.** The polynomial hash uses base 31, modulus 101 and ASCII character codes. For a length-`m` window, the leftmost character has coefficient `31^(m-1)`. The same calculation is performed for the pattern and the first text window.

**Rolling update.** Remove the outgoing character multiplied by `31^(m-1)`, reduce modulo 101, multiply by 31, then add the incoming character. Python's modulo operation normalizes the result to a non-negative remainder.

**Correctness.** Unequal hashes prove the strings differ, but equal hashes only identify a candidate. Every equal-hash window is compared character by character before reporting. Therefore collisions cannot create false matches. The scan visits every legal start, preserving overlaps. Empty and too-long patterns are handled before a window is formed.

**Complexity.** Initial hashing is `O(m)` and each rolling update is `O(1)`. If `c` windows have the pattern's hash, verification costs up to `O(c*m)`, giving `O(n+m+c*m)` time for nonempty patterns with `m<=n`; worst case can be quadratic. Auxiliary memory is `O(1)` beyond the output list.

**Boundary/collision test.** Text `"abdj"`, pattern `"ab"` has an equal-hash nonmatching window at `"dj"` with base 31/modulus 101. Only position zero may be returned. This catches treating hash equality as proof of string equality.

### 7. `suffix` — prefix-doubling suffix array and Kasai LCP

**Suffix-array state.** `sa` stores starting indices of nonempty suffixes. Initially, ranks are character codes. At doubling length `k`, each suffix is sorted by the pair `(rank[i], rank[i+k])`, using `-1` when the second half is beyond the text. New equivalence-class ranks are assigned in sorted order.

**Processing order and correctness.** Initially, ranks order one-character prefixes. If ranks correctly order prefixes of length `k`, sorting rank pairs orders prefixes of length up to `2k`. Repeating with doubled `k` eventually distinguishes all finite suffixes; the `-1` end marker orders a shorter suffix before a longer suffix with the same prefix. The implementation sorts indices by rank pairs and never materializes suffix strings.

**Kasai state.** `inverse[i]` is the position of suffix `i` in `sa`. `lcp[p]` is the common-prefix length of `sa[p-1]` and `sa[p]`, with `lcp[0]=0`. Kasai compares each suffix with its previous suffix in suffix-array order. When moving from text position `i` to `i+1`, the known common prefix can decrease by at most one, so `h-1` is a valid starting lower bound. If a suffix is first in suffix order, `h` is reset to zero.

**Longest repeat.** The longest repeated substring is the maximum adjacent LCP. Any two suffixes sharing a prefix have all suffixes between them in lexicographic order sharing at least that prefix at some adjacent boundary; consequently the maximum common prefix among any pair is attained by an adjacent pair. The substring is read from the corresponding suffix start. Overlaps are allowed.

**Complexity.** Prefix doubling uses `O(log n)` rounds, each comparison sort taking `O(n log n)`, for `O(n log^2(n+1))` time. Kasai is `O(n)`. Rank, inverse, LCP and suffix arrays use `O(n+1)` auxiliary/output memory. Empty text returns empty arrays and an empty repeated string.

**Boundary test.** `"aaaa"` must produce suffix order `[3,2,1,0]`, LCP `[0,1,2,3]` and longest repeat `"aaa"`. This catches missing suffixes, an incorrect end-of-text rank, or disallowing overlapping repeats.

### 8. `aho` — Aho–Corasick multi-pattern matching

**Trie and states.** Each trie state represents a dictionary prefix. The implementation uses a compact 95-entry transition array for printable ASCII characters (codes 32–126). Duplicate patterns share the same terminal state, while that state's terminal ID list preserves every original dictionary position.

**Failure links.** Breadth-first construction sets each child's failure link to the state reached by following the parent's failure transition on the same character. Missing transitions are completed from the failure state, so each text character then takes one automaton transition. BFS ensures a failure state's transitions are already complete.

**Counting and suffix patterns.** While scanning one text, the algorithm increments a visit count for the reached state. A pattern ending at a failure ancestor is also a match. Instead of walking output links for every match, visit counts are propagated to failure parents in reverse BFS order. Each terminal state's final count is copied to all original pattern IDs ending there. This counts suffix patterns, overlaps and duplicates without expanding a large output list.

**Independent texts and correctness.** The automaton is built once per request. Each text gets a fresh visit array and starts at the root, so counts cannot leak between texts. Every pattern occurrence ends at exactly one reached state; propagation adds that occurrence to each terminal state on its failure chain. Therefore each pattern's count is exact, including suffix matches.

**Complexity.** Let `L` be total pattern length including duplicates, `S` the number of trie states and `p` the number of patterns. Building trie transitions and terminal IDs takes `O(L)`. Completing 95 transitions per state takes `O(95*S)` time and memory; BFS failure construction is included in this bound. For each text of length `t`, scanning and reverse failure propagation take `O(t+S+p)` including output row creation. Output memory is `O(q*(p+1)+1)` for `q` texts; auxiliary automaton memory is `O(95*S+p)`.

**Boundary test.** Patterns `["he","she","he"]` in text `"sheshe"` must each count two occurrences. This catches failure-link suffix omissions and duplicate-pattern handling errors. A second empty text must produce a row of zeros.

## Own tests

The additional tests are in `tests/student/test_algorithms.py`. They use fixed random seeds so the test data is reproducible.

| Command/group | Input or fixture | Expected result | Actual result | What it checks |
|---|---|---|---|---|
| LCS | 100 random pairs over `abc`, lengths below 9 | Optimal length; returned sequence is a subsequence of both strings | Passed | DP value and reconstruction against exhaustive subsequence enumeration |
| Merge | 120 random arrays, lengths 0–7 | Exactly `n-1` legal chronological adjacent merges and reported cost equal to plan cost | Passed | Interval boundaries and plan reconstruction |
| Tree | 250 random trees, up to 10 vertices | Maximum weight among all vertex subsets; no selected edge endpoints | Passed | Take/skip DP, negative weights and reconstruction against brute force |
| Naive/KMP/RK | 250 random text/pattern pairs | Same positions as direct `startswith` oracle, including empty patterns | Passed | Exact matching, overlaps and empty-pattern contract |
| Suffix | 250 random strings, lengths below 30 | Same order as sorting suffixes; exact adjacent LCP; valid longest repeat | Passed | Prefix doubling, Kasai and repeated substring |
| Aho–Corasick | 100 random dictionaries/text batches | Exact per-pattern counts from direct occurrence counting | Passed | Failure propagation, duplicates, overlaps and independent texts |
| Tree stress | 100,000-vertex chain | Weight 50,000 and 50,000 selected vertices | Passed | Iterative traversal avoids recursion failure |
| Published-domain smoke checks | LCS 1000×1000; merge n=200; tree n=100000; suffix n=50000; Aho 1000 nested patterns | Valid output sizes and no timeout | Passed | Upper-bound input handling and practical runtime |

Public validation: `python tools/run.py --check` passed all 44 public cases and the repeated mixed-batch state-reset check. Student validation: `python -m unittest discover -s tests/student -v` passed all 7 test methods.

## Search comparison

All three algorithms were timed on identical input strings at `n = 300, 1000, 3000`, with `m = floor(n/3)`. The random case used Python's `random.Random(20261108)` to generate a lowercase text; the pattern was a length-`m` substring starting at `n//2`, guaranteeing one occurrence. The repetitive case used text `"a"*n` and pattern `"a"*m`, producing `n-m+1` overlapping matches and many Rabin–Karp hash candidates. All three outputs were checked for exact equality before and during timing. Each cell below gives three raw runs in milliseconds followed by their median. Timing covers the function call and result-list construction; it excludes JSON parsing and process startup. There was no JIT compilation or compilation warm-up. Values are environment-specific observations, not complexity proofs.

| Case | n | m | Seed / generator | Algorithm | Run 1 (ms) | Run 2 (ms) | Run 3 (ms) | Median (ms) | Correct outputs checked |
|---|---:|---:|---|---|---:|---:|---:|---:|---|
| Random | 300 | 100 | seed 20261108, lowercase | Naive | 0.016 | 0.016 | 0.015 | 0.016 | Yes |
| Random | 300 | 100 | same | KMP | 0.021 | 0.019 | 0.019 | 0.019 | Yes |
| Random | 300 | 100 | same | RK | 0.044 | 0.042 | 0.041 | 0.042 | Yes |
| Random | 1,000 | 333 | same | Naive | 0.057 | 0.056 | 0.056 | 0.056 | Yes |
| Random | 1,000 | 333 | same | KMP | 0.131 | 0.119 | 0.069 | 0.119 | Yes |
| Random | 1,000 | 333 | same | RK | 0.280 | 0.144 | 0.142 | 0.144 | Yes |
| Random | 3,000 | 1,000 | same | Naive | 0.203 | 0.174 | 0.173 | 0.174 | Yes |
| Random | 3,000 | 1,000 | same | KMP | 0.211 | 0.208 | 0.221 | 0.211 | Yes |
| Random | 3,000 | 1,000 | same | RK | 0.718 | 0.550 | 0.580 | 0.580 | Yes |
| Repetitive | 300 | 100 | `a` repeated | Naive | 0.958 | 1.000 | 0.932 | 0.958 | Yes |
| Repetitive | 300 | 100 | same | KMP | 0.034 | 0.074 | 0.031 | 0.034 | Yes |
| Repetitive | 300 | 100 | same | RK | 0.558 | 0.745 | 0.829 | 0.745 | Yes |
| Repetitive | 1,000 | 333 | `a` repeated | Naive | 11.482 | 11.001 | 11.988 | 11.482 | Yes |
| Repetitive | 1,000 | 333 | same | KMP | 0.147 | 0.122 | 0.119 | 0.122 | Yes |
| Repetitive | 1,000 | 333 | same | RK | 7.476 | 7.425 | 6.980 | 7.425 | Yes |
| Repetitive | 3,000 | 1,000 | `a` repeated | Naive | 110.447 | 114.760 | 109.525 | 110.447 | Yes |
| Repetitive | 3,000 | 1,000 | same | KMP | 0.564 | 0.381 | 0.486 | 0.486 | Yes |
| Repetitive | 3,000 | 1,000 | same | RK | 74.311 | 78.563 | 71.961 | 74.311 | Yes |

**Observations.** On the random inputs, the naive algorithm is competitive because most candidate windows fail quickly. On repetitive inputs, it compares many characters for many candidate starts, showing its `O(n*m)` worst-case behavior. KMP remains fast because it reuses prefix information and runs in linear time. Rabin–Karp is especially slow on the repetitive case because every window has the same hash and must be verified character by character. The modulus 101 is deliberately small, so collisions are easy to encounter; these measurements must not be generalized to larger production hash choices. Hash equality is never accepted without exact character verification.

## Sources and AI assistance

- Assignment 4 specification and request contracts supplied with the course template: `docs/Assignment_4_EN.md` and `docs/guide/CONTRACTS.md`.
- Course template launcher and public validator: `tools/run.py` and `tools/public_validate.py`.
- AI assistance was used to help implement and review the Python algorithms, prepare additional tests and draft this analysis. The student should review the code, understand each recurrence/invariant, run the commands above on their own machine, verify the results, and be prepared to explain and defend the implementation independently.
