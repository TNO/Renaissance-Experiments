# Position consistency

{ #dev-architecture-code-position-consistency }

**Stable ID:** `ARCH-CODE-POSITION-CONSISTENCY`

## Purpose

Document the design decisions that guarantee that the [rewrite](modify.md) step and the parser agree on
what a node's position (offset, length) in the source text means.

## Scope

This document covers how a node's position is bound to the source buffer it was computed from, so
that a rewrite can never apply a position under a different assumption (encoding, unit, or buffer)
than the one the parser used when it built the node.

It does not cover how multiple changes are combined once their positions are known to be consistent -
see [Rewrite semantics](rewrite-semantics.md) for that.
It does not cover the definition of the rewrite step itself - see [Modify](modify.md).

## Definition

Every node exposes an `offset` and `length` (or `end_offset`), and is navigable to its root via `parent`
(see [Code architecture](code-architecture.md)). The root is the same object, produced by the same
parser invocation, that the buffer and every offset in the tree were derived from.

A node may also expose a line and column for a given offset, for use in diagnostics and other
human-facing interactions. Line/column is not itself used to apply a rewrite - only `offset`/`length`
index directly into the buffer being patched - but it is subject to the same consistency requirement,
since it locates the same position in the same source text.

### Line and column as a derived representation

Line and column cannot be computed independently of `offset` without risking the same disagreement
this document addresses: a parser may compute line/column using its own line-splitting or encoding
assumption, which need not match the buffer the rewriter patches (e.g. CPython's `ast` module
reports `lineno`/`col_offset` relative to each line, which then needs a conversion back to a global
offset).

**Decision**

Line and column are derived from a node's `offset` using a single line-index built once from the
node's root buffer, not independently computed or cached per node from a separate source. A node's
`offset` remains the single source of truth for its position; line and column are a presentation of
that same offset.

### Guaranteeing agreement between parser and rewriter

A rewrite reads a node's position and splices replacement text into a byte buffer at that position.
This is only correct if the buffer being patched is the same buffer, encoded the same way, that the
parser used to compute the node's position in the first place. If the rewriter independently
reconstructs a buffer - for example, by re-encoding a node's text using an unrelated, ambient encoding -
the two sides can silently disagree, producing incorrect or corrupted output.

**Options considered**

* Structural rewriting: mutate the tree and let the parser's own printer regenerate text, so no
  separate offset bookkeeping exists (as used for Python, see
  [ADR 11](adr/11_parser_with_space_and_comment.md)). Not available for every integration, since
  not every parser provides a lossless printer.
* Wrap positions in a new value type (e.g. `Span`/`SourceFile`) that binds an offset to the buffer
  it was computed from. Rejected as redundant: the node already carries everything needed (offset,
  length, and a path to its root) without introducing a new type.
* Compare source file paths to decide whether two nodes' positions are comparable. Rejected: the
  same path can back different buffers at different times (e.g. a stale tree held before a reparse,
  a file re-read after an on-disk edit, or two different node representations for the same language
  parsed from the same file). Path equality would wrongly treat these as compatible.

**Decision**

1. A rewrite batch is scoped to a single root.
2. Nodes are accepted into the same rewrite batch only if they share that root, checked by object
   identity (`is`), not by file path or any other derived key.
3. The byte buffer used to apply a rewrite batch is obtained from the root itself, not re-derived
   by re-encoding node text.
4. A mismatch is rejected immediately (fail fast) rather than silently applied.

## Invariants / guarantees

* All nodes involved in a single rewrite batch share the same root object.
* The buffer patched by a rewrite is the same buffer the parser produced the involved nodes' offsets
  from.
* A rewrite across nodes with different roots is rejected rather than silently applied.
* A node's line and column, if exposed, are derived from its `offset` and its root's buffer, not
  independently computed.

## Related features

* [Modify](modify.md)
* [Rewrite semantics](rewrite-semantics.md)

## Related tests

## Related code

## Notes
