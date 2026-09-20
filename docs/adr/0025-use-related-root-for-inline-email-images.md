# ADR 0025: Use a related root for inline email images

## Decision

An HTML Digest with an inline image is encoded with `multipart/related` at the
root. Its first child is `multipart/alternative`, containing sibling
`text/plain` and `text/html` parts, and its second child is the CID-addressed
image. A Digest without inline images remains a root `multipart/alternative`.

The plain-text part contains the actual Digest title, date, article titles,
URLs, summaries, reasons to read, tags, and retrieval failures. It is no longer
only an instruction to use an HTML-capable client.

This is a standards-oriented MIME layout rather than a client-specific branch.
It lets clients choose directly between plain text and HTML while preserving the
HTML-to-image relationship.
