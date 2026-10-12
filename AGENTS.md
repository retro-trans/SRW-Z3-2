** Organize folder like this **
work - work folder
    output - contains the file for testing (iso, zip, etc...)
    glossary - contains the one or many json files for glossary
    ui - contains screenshot of actual UI element ingame with label on screenshot if possible, contains files (json,py,...) describe the coordinate, width and height, id and other attributes
    translation/<language code> - contains the target translation of ui element or dialogues or anything that need translation
docs - documents
tools - any tools help with translation
incoming - outside files that need agent to look into

** SOME RULES **
- Avoid contains extensive Japanese scripts (UI elements is fine)
- Identified each build with version 0.x.y (start at 0.1.0)
- Always write change log
- If user told you to remember anything write it down here, make sure to ask user if the new one conflict with old one
- Consider using https://github.com/nationalsecurityagency/ghidra if applicable

** REMEMBER **
- Every new release must work with [Retro Trans Tools](https://github.com/retro-trans/retro-trans-tools).
- The user always tests the public release. Prepare fixes and validated Retro Trans patches for public delivery; a separate local testing ISO does not reach their normal testing workflow. Creating or publishing a GitHub release requires the user's explicit consent for that release. The user accepted 0.5.18 as a one-time exception; this does not authorize future releases.
- Canonical spellings requested on 2026-10-12: Heero Yuy (both pilot and historical leader), Crowe Bluest. Proofreading must preserve these spellings. Yui Ikari remains Yui.
- Additional canonical spellings requested on 2026-10-12: Sacks (not Sachs), Giltar (not Girtar). Apply them throughout active text and preserve them during proofreading.
- Canonical location spelling requested on 2026-10-12: Ameria (not Amerria). Apply it throughout active text and preserve it during proofreading.
- Canonical Godmars name requested on 2026-10-13: Zuul (Emperor Zuul), not Xul or Zul. Apply it throughout active text and preserve it during proofreading.
