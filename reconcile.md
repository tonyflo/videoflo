# Reconcile an existing Mac channel with Planka

Run `python3 reconcile.py --help` for options. This is a local reconciliation command:
it reads the configured Planka board, never creates/moves/deletes remote cards, and
previews all actions unless `--apply` is supplied.

- `--match 'FOLDER=CARD TITLE'` confirms a title/folder match (or use a card ID).
- `--trash FOLDER ...` moves the named local folders to the Mac Trash.
- `--ignore FOLDER ...` leaves the named folders alone.
- Existing links and unique filename/title matches are reused.
- Remaining supported-stage cards get new folders with camera/, notes.txt,
  .planka-card, .stage and the corresponding Finder workflow tag.
- Unrelated unmatched folders are kept. Ambiguous existing matches block application.
- All nine stages, including Published, are included. Archived/trash cards are excluded.
- The script never renames existing media folders or overwrites their files.

First run without --apply and review every CREATE/LINK/TRASH line.
Then rerun the same arguments with --apply. Reruns use saved card IDs to avoid duplicates.

Regression cases are in tests/test_reconcile.py. They were added during a turn
without an execution workspace and have not been run yet:
`python3 -m unittest discover -s tests -v`.
