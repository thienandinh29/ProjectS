# Verification status — 24 September 2026

## Passed

- 29 automated tests: all Vietnamese characters/tones, uppercase, normal
  sentences, traditional/modern placement, literal English Telex triggers,
  Unicode normalization, unsupported-character offsets and limits.
- Corrections simulated against the vendored upstream UniKey core, including
  backspaces and preservation of a pre-existing prefix; seeded full-text
  comparisons with corrections enabled and disabled.
- UTF-8/UTF-16, DOCX paragraphs and merged table cells, malformed files, link
  parsing, mocked public/private Google responses, login redirects and failures.
- Playback cancellation before input, during countdown, long pauses and
  backspaces; focus loss; failure to establish stop monitoring.
- Windows native structure sizes and refusal to send input without arming.
- Hidden Tkinter interface startup and control-state test under the normal
  Windows account. The restricted sandbox could not load Tcl/Tk; the same
  test passed outside it without sending any keyboard input.
- Packaged `GoViet.exe` self-test: offline Telex oracle, Word/text dependencies
  and hidden interface startup passed with exit code 0. No keyboard input was
  sent. Source ZIP integrity was checked; no virtual environment, Git metadata
  or user-content files are included.

## Not verified live

Actual keystroke injection into Google Docs with the installed Windows UniKey
in Chrome or Edge, physical F8/hook behavior in those browsers, Google network
imports and Google version-history behavior have not been live-tested.

Computer Use ended during Chrome inspection because its tool could not verify
the current browser URL with enough confidence to enforce policy. No document
typing test was performed through that tool.

The application therefore requires a real scratch-document trial and exact
copy-back comparison before enabling full typing. Offline engine tests do not
replace this browser/UniKey compatibility check. See the guide for setup.
