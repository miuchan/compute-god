# Incremental Construction of Minimal Acyclic Finite-State Automata

Incremental construction techniques build deterministic finite-state automata (DFAs) directly from a stream of sorted input strings while maintaining minimality throughout the process. Compared with classical two-pass approaches that first build a trie and then minimize it, an incremental minimal DFA algorithm combines state creation, merging, and minimization in a single pass. This results in lower memory requirements and enables online construction.

## Problem Statement

Given a lexicographically sorted list of strings over a finite alphabet, construct a minimal deterministic acyclic finite-state automaton (DAFSA) that accepts exactly the given strings. The automaton must remain minimal after each string is processed.

## Core Ideas

1. **Lexicographic Ordering** – Processing strings in lexicographic order ensures that each new string shares the longest possible prefix with the previously processed one. The divergence point marks where new states must be created.
2. **Register of Representatives** – Maintain a dictionary keyed by the right-language (the set of suffixes accepted from a state) representation of states. Whenever a new state is finalized, attempt to replace it with an equivalent registered state.
3. **Incremental Minimization** – When finishing a word, recursively minimize the suffix of the path that was unique to that word by examining the states from deepest to shallowest. Equivalent states are merged immediately.
4. **Acyclic Guarantee** – Because the input words are processed in increasing order, edges always point from shallower prefixes to deeper suffixes, preventing cycles.

## Algorithm Outline

1. Initialize the automaton with a single root state and an empty register.
2. For each input word:
   - Determine the length of the longest common prefix with the previous word.
   - **Minimize**: traverse the path of states created by the previous word beyond the common prefix from deepest to just beyond the shared prefix. For each state:
     - Serialize its outgoing transitions and finality to form a signature.
     - If an equivalent state exists in the register, replace the transition pointing to the current state with the registered representative; otherwise, add the current state to the register.
   - **Extend**: starting from the node at the common prefix, create new states for the remaining suffix of the current word, linking transitions along the characters.
   - Mark the state corresponding to the end of the word as final.
3. After processing all words, minimize the remaining branch originating from the root.

## State Signature Representation

A state signature captures finality and the lexicographically sorted list of outgoing transitions.

```
Signature(state) = (is_final(state), [(symbol_1, target_id_1), ..., (symbol_k, target_id_k)])
```

Using immutable ordered tuples for transitions ensures that two states with identical right-languages receive the same signature.

## Complexity and Storage

- **Time Complexity**: Each word is processed in time proportional to its length, plus the cost of hashing signatures. Because each state is created and minimized once, overall time is linear in the total number of characters across all words.
- **Space Complexity**: Only the current branch and register are required. For n words, the number of simultaneously unregistered states is bounded by the length of the previous word.

## Example

Consider the sorted input: {"cat", "catalog", "cater", "dog"}.

1. Process "cat": create states for `c → a → t`, mark `t` as final.
2. Process "catalog": longest common prefix `"cat"`.
   - Minimize suffix from previous word (no change as only `t` leaf exists).
   - Extend by adding states for `a → l → o → g` from the state at `t`.
3. Process "cater": longest common prefix `"cat"`.
   - Minimize suffix from previous word (`alog` branch). All states remain unique.
   - Extend by adding `e → r` from `t`.
4. Process "dog": longest common prefix is empty.
   - Minimize branch for `"cater"`, merging shared suffixes where possible.
   - Create new branch for `d → o → g` and mark `g` final.

The resulting automaton merges equivalent suffixes and maintains minimality after each step.

## Practical Considerations

- **Implementation Data Structures**: adjacency lists or dictionaries keyed by symbols work well. Hash tables for the register allow constant-time lookup of signatures.
- **Streaming Inputs**: The algorithm supports online updates as long as the new string is lexicographically greater than the previous ones. For unsorted inputs, sort them first or apply a buffering strategy.
- **Unicode and Large Alphabets**: When dealing with wide alphabets, compress the transition table or use integer encoding for symbols to reduce signature size.
- **Persistence**: To serialize the automaton, store states with unique IDs, final markers, and transitions sorted by symbol for determinism.

## Further Reading

- Jan Daciuk, Stoyan Mihov, Bruce W. Watson, and Richard E. Watson. "Incremental Construction of Minimal Acyclic Finite-State Automata." *Computational Linguistics* 26(1): 3–16, 2000.

