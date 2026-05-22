# Lookup Data

`lookup.sqlite` is the compiled lookup database used by Lot Plotter at runtime.
It is generated from the lookup source files in this folder with:

```powershell
python tools\compile_lookupdata.py
```

The plugin prefers `lookup.sqlite` when it exists and falls back to the source
CSV/TXT/DTA files when it does not.

Before publishing a public plugin package, verify that every lookup dataset and
spreadsheet you include is owned by you or licensed for redistribution. If you
ship only the compiled database, keep the source files in the repository or in a
private archive only when the license/provenance allows it.
