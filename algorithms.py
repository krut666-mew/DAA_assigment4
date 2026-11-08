"""Implementations for Assignment 4: Dynamic Programming and String Processing."""
from collections import deque
from array import array


def lcs(request):
    """Return the length and one longest common subsequence of a and b."""
    a, b = request["a"], request["b"]
    n, m = len(a), len(b)
    if not n or not m:
        return {"length": 0, "sequence": ""}

    # dp[i][j] is the LCS length of a[:i] and b[:j].
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        row, previous = dp[i], dp[i - 1]
        ai = a[i - 1]
        for j in range(1, m + 1):
            if ai == b[j - 1]:
                row[j] = previous[j - 1] + 1
            else:
                row[j] = max(previous[j], row[j - 1])

    # Walk backwards through the table and then reverse the chosen characters.
    i, j = n, m
    result = []
    while i and j:
        if a[i - 1] == b[j - 1]:
            result.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    result.reverse()
    return {"length": dp[n][m], "sequence": "".join(result)}


def merge(request):
    """Minimum-cost adjacent interval merging with a chronological merge plan."""
    sizes = request["sizes"]
    n = len(sizes)
    if n <= 1:
        return {"cost": 0, "plan": []}

    prefix = [0] * (n + 1)
    for i, value in enumerate(sizes):
        prefix[i + 1] = prefix[i] + value

    # dp[left][right] is the minimum cost to merge that closed interval.
    dp = [[0] * n for _ in range(n)]
    split = [[-1] * n for _ in range(n)]
    for length in range(2, n + 1):
        for left in range(n - length + 1):
            right = left + length - 1
            interval_sum = prefix[right + 1] - prefix[left]
            best = None
            best_k = -1
            for k in range(left, right):
                candidate = dp[left][k] + dp[k + 1][right] + interval_sum
                if best is None or candidate < best:
                    best, best_k = candidate, k
            dp[left][right] = best
            split[left][right] = best_k

    # Explicit postorder traversal: children are merged before their parent.
    plan = []
    stack = [(0, n - 1, False)]
    while stack:
        left, right, emit = stack.pop()
        if left == right:
            continue
        if emit:
            plan.append([left, split[left][right], right])
        else:
            k = split[left][right]
            stack.append((left, right, True))
            stack.append((k + 1, right, False))
            stack.append((left, k, False))
    return {"cost": dp[0][n - 1], "plan": plan}


def tree(request):
    """Maximum-weight independent set of a tree; iterative to support deep trees."""
    n = request["n"]
    weights = request["weights"]
    if n == 0:
        return {"weight": 0, "selected": []}

    graph = [[] for _ in range(n)]
    for u, v in request["edges"]:
        graph[u].append(v)
        graph[v].append(u)

    # Build a rooted traversal without recursion (a chain may have 100,000 nodes).
    parent = [-1] * n
    parent[0] = 0
    order = [0]
    for u in order:
        for v in graph[u]:
            if v != parent[u]:
                parent[v] = u
                order.append(v)

    take = [0] * n
    skip = [0] * n
    for u in reversed(order):
        take_u = weights[u]
        skip_u = 0
        for v in graph[u]:
            if parent[v] == u:
                take_u += skip[v]
                skip_u += max(take[v], skip[v])
        take[u] = take_u
        skip[u] = skip_u

    optimum = max(take[0], skip[0])
    selected = []
    # Reconstruct with a stack; ties choose skip, which is also optimal.
    stack = [(0, False)]
    while stack:
        u, parent_taken = stack.pop()
        choose = (not parent_taken) and take[u] > skip[u]
        if choose:
            selected.append(u)
        for v in graph[u]:
            if parent[v] == u:
                stack.append((v, choose))
    return {"weight": optimum, "selected": selected}


def naive(request):
    """Naive exact substring search, including overlaps and empty patterns."""
    text, pattern = request["text"], request["pattern"]
    n, m = len(text), len(pattern)
    if m == 0:
        return {"positions": list(range(n + 1))}
    if m > n:
        return {"positions": []}
    positions = []
    for start in range(n - m + 1):
        j = 0
        while j < m and text[start + j] == pattern[j]:
            j += 1
        if j == m:
            positions.append(start)
    return {"positions": positions}


def _prefix_function(pattern):
    """pi[i] is the longest proper prefix that is also a suffix of pattern[:i+1]."""
    pi = [0] * len(pattern)
    j = 0
    for i in range(1, len(pattern)):
        while j and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j
    return pi


def kmp(request):
    """Knuth-Morris-Pratt exact search with linear-time prefix fallback."""
    text, pattern = request["text"], request["pattern"]
    n, m = len(text), len(pattern)
    if m == 0:
        return {"positions": list(range(n + 1))}
    if m > n:
        return {"positions": []}

    pi = _prefix_function(pattern)
    positions = []
    j = 0
    for i, char in enumerate(text):
        while j and char != pattern[j]:
            j = pi[j - 1]
        if char == pattern[j]:
            j += 1
        if j == m:
            positions.append(i - m + 1)
            j = pi[j - 1]  # Preserve overlapping matches.
    return {"positions": positions}


def rk(request):
    """Rabin-Karp with the required base/modulus and exact candidate verification."""
    text, pattern = request["text"], request["pattern"]
    n, m = len(text), len(pattern)
    if m == 0:
        return {"positions": list(range(n + 1))}
    if m > n:
        return {"positions": []}

    base, modulus = 31, 101
    highest_power = pow(base, m - 1, modulus)
    pattern_hash = 0
    window_hash = 0
    for i in range(m):
        pattern_hash = (pattern_hash * base + ord(pattern[i])) % modulus
        window_hash = (window_hash * base + ord(text[i])) % modulus

    positions = []
    for start in range(n - m + 1):
        if window_hash == pattern_hash:
            # A hash collision is not an exact string match.
            equal = True
            for j in range(m):
                if text[start + j] != pattern[j]:
                    equal = False
                    break
            if equal:
                positions.append(start)
        if start < n - m:
            outgoing = ord(text[start])
            incoming = ord(text[start + m])
            window_hash = (window_hash - outgoing * highest_power) % modulus
            window_hash = (window_hash * base + incoming) % modulus
    return {"positions": positions}


def suffix(request):
    """Prefix-doubling suffix array, Kasai LCP, and a longest repeated substring."""
    text = request["text"]
    n = len(text)
    if n == 0:
        return {"sa": [], "lcp": [], "repeated": ""}

    # Initial ranks are character codes. Each round sorts (rank[i], rank[i+k]).
    sa = list(range(n))
    rank = [ord(ch) for ch in text]
    k = 1
    while k < n:
        sa.sort(key=lambda i: (rank[i], rank[i + k] if i + k < n else -1))
        new_rank = [0] * n
        classes = 0
        new_rank[sa[0]] = 0
        for pos in range(1, n):
            prev, cur = sa[pos - 1], sa[pos]
            prev_pair = (rank[prev], rank[prev + k] if prev + k < n else -1)
            cur_pair = (rank[cur], rank[cur + k] if cur + k < n else -1)
            if cur_pair != prev_pair:
                classes += 1
            new_rank[cur] = classes
        rank = new_rank
        if classes == n - 1:
            break
        k <<= 1

    # Kasai: reuse h-1 after moving from suffix i to suffix i+1.
    inverse = [0] * n
    for position, start in enumerate(sa):
        inverse[start] = position
    lcp = [0] * n
    h = 0
    for i in range(n):
        pos = inverse[i]
        if pos == 0:
            h = 0
            continue
        j = sa[pos - 1]
        while i + h < n and j + h < n and text[i + h] == text[j + h]:
            h += 1
        lcp[pos] = h
        if h:
            h -= 1

    best_length = max(lcp)
    repeated = ""
    if best_length:
        best_position = lcp.index(best_length)
        repeated = text[sa[best_position]:sa[best_position] + best_length]
    return {"sa": sa, "lcp": lcp, "repeated": repeated}


def aho(request):
    """Aho-Corasick DFA with reverse failure-link visit aggregation."""
    patterns, texts = request["patterns"], request["texts"]
    # The contract alphabet is printable ASCII (32..126). A compact signed
    # integer array stores all 95 transitions for each state; state 0 means
    # "missing" during trie construction and is also the root state.
    alphabet_size = 95
    transitions = [array("i", [0]) * alphabet_size]
    failure = [0]
    terminal_ids = [[]]
    for pattern_id, pattern in enumerate(patterns):
        state = 0
        for char in pattern:
            code = ord(char) - 32
            nxt = transitions[state][code]
            if nxt == 0:
                nxt = len(transitions)
                transitions[state][code] = nxt
                transitions.append(array("i", [0]) * alphabet_size)
                failure.append(0)
                terminal_ids.append([])
            state = nxt
        terminal_ids[state].append(pattern_id)

    # Complete every transition in BFS order. Failure links always point to
    # a shallower state, so its transitions are ready before this state.
    queue = deque()
    bfs_order = [0]
    for code in range(alphabet_size):
        child = transitions[0][code]
        if child:
            queue.append(child)
            bfs_order.append(child)

    while queue:
        state = queue.popleft()
        fallback_row = transitions[failure[state]]
        row = transitions[state]
        for code in range(alphabet_size):
            child = row[code]
            if child:
                failure[child] = fallback_row[code]
                queue.append(child)
                bfs_order.append(child)
            else:
                row[code] = fallback_row[code]

    rows = []
    pattern_count = len(patterns)
    for text in texts:
        visits = [0] * len(transitions)
        state = 0
        for char in text:
            state = transitions[state][ord(char) - 32]
            visits[state] += 1

        # Each state visit also represents every suffix on its failure chain.
        # Reverse BFS order propagates all counts in O(number of states).
        for node in reversed(bfs_order[1:]):
            visits[failure[node]] += visits[node]

        row = [0] * pattern_count
        for node, ids in enumerate(terminal_ids):
            count = visits[node]
            if count:
                for pattern_id in ids:
                    row[pattern_id] = count
        rows.append(row)
    return {"counts": rows}
