# Ukrainian (`ukua`) Language Support - Progress and Resume Guide

This document tracks the end-to-end development, architecture decisions, current status, and step-by-step instructions for the native Ukrainian language module in OpenEVV.

## Core Design Principles

1. **Native Integration**: Ukrainian is implemented as an authentic OpenEVV language module (`lang/ukua`), maintaining Eloquence's Klatt formant acoustic character and single-binary multi-language support.
2. **RHVoice Phonetics**: Phoneme definitions and G2P pronunciation rules follow RHVoice's Ukrainian phonetic models (handling hard/soft consonants, palatalization before `ь`, iotated vowels `я, ю, є, ї`, and consonant assimilation).
3. **Word Stress Dictionary**: Word stress is sourced from `lang-uk/ukrainian-word-stress-dictionary` (over 2.9 million words derived from ULIF).
4. **Cloud-First Compilation (GitHub Actions CI)**: Heavy compilation, dictionary ingestion, matrix checks, and binary releases (`probe.exe`, `eci.dll`, audio samples) are built in GitHub Actions CI to avoid local download and compute bottlenecks.
5. **Granular Git Commits**: Every change and step is committed individually with descriptive messages.

## Language Metadata

- **Language Tag**: `ukua`
- **Language Name**: `Ukrainian`
- **Family ID**: `18` (`0x12`)
- **Dialect ID**: `0`
- **ECI Full Language Code**: `0x120000`
- **Chassis**: Polish (`lang/plpl`)
- **Settings Section**: `[18.0]`, `eciukua.syn`, `Static Engine UKR`

## Development Roadmap & Status

### Phase 1: Engine Multi-Language Scalability
- [x] Expand engine family capacity: FAMILIES to 32 in statics and voicetable, RM_FAMILIES and ROM_FAMILIES to 32 with resized RomanizerManager arrays, and DICT_FAMILIES to 19 (safely bounding ed_deactivate_all_dicts within OldInst).
- [x] Register `ukua` in `tools/module/gather.py`.
- [x] Verify zero regressions in existing 10 languages.

### Phase 2: Ukrainian Module Chassis Setup
- [ ] Fork `lang/plpl` chassis to `lang/ukua`.
- [ ] Rename symbols and file headers from `plpl` to `ukua`.
- [ ] Update `ukua.settings` for Language ID `[18.0]` and Ukrainian voice profiles.
- [ ] Update `ukua.globals` and statement references.

### Phase 3: Cyrillic Alphabet & UTF-8 Codepoints
- [x] Define the 33 Ukrainian Cyrillic letters in `ukua.statements`. The chassis was Italian and its 33 accented-Latin lower-case slots were unused, so each was repurposed in place with `tools/module/alphabet.py set` (byte and name unchanged, only the 5-byte record rewritten) — no code keyed on a byte shifts. Bytes `0xC0`–`0xE1` (skipping `0xD7` `×`) carry the letters in alphabet order; `0xE2` carries the combining stress mark, typed `acute_acc`.
- [x] Create `lang/ukua/ukua.codepoints` mapping Unicode Cyrillic to those bytes: 33 lower-case letters, 33 capitals each folded onto its own lower-case byte (so the engine never sees a capital to fold), the combining acute `U+0301`→`0xE2`, and the two Unicode apostrophes `U+2019`/`U+02BC`→`0x27`.
- [x] Compile `delta_codepoints_ukua.c` (69 entries) via `tools/module/codepoints.py ukua`. UTF-8 input recoding in `addTextRun` is exercised in CI.
- [x] Fix the stale `delta_consts_plpl.c` reference in `lang/ukua/rules/symbols`.

> Note: the plan's Task 3 proposed bytes `0x80`–`0xDF`, but the low half of
> that range is claimed by Italian letters the chassis still carries. The
> reclaim above (accented-Latin slots, records only) realises the same intent
> without renumbering any existing code point.

### Checkpoint (2026-09-25): 30/33 letters speaking, real audio in CI

Phase 3 is verified green across all six CI builds and the engine produces real
Ukrainian audio: `привіт`→`[.0pri.1vit]`, `Слава Україні`→ a 15 004-sample wav,
and the phrase set→ a 52 360-sample wav. Thirty of the thirty-three Cyrillic
letters render correctly through the own-arm (`pol_test_own_letters` →
`apply_pol_letter_rules` in `it_phone.up`), including the two-phone `ї`→`j i`.

Three letters are **parked, pending the Phase-5 G2P layer**, because they cannot
be voiced by repurposing an Italian letter byte:

- **`я` /ja/ and `ю` /ju/** are iotated (two phones each). Reaching the own-arm
  needs a latin-1 byte Italian's letter-to-sound leaves untouched, and there is
  none free: Italian folds every lower-case latin-1 letter (accented vowels to a
  base; `ð`→d, `þ`→drop, `ß`→ss, `æ`→a, `ø`→c), and the only bytes it ignores —
  the upper-case block `c0`–`de` — are the thirty non-iotated letters, full.
  (Proven across five CI rounds relocating the pair onto `e0/e1`, `82/84`,
  `86/87`, `d7/a2`, `q`/`df`, `þ`/`ð`, and `æ`/`ø`.) They are therefore parked on
  the bytes Italian folds to their bare nucleus — `я` on `æ` (e6)→`/a/`, `ю` on
  `ù` (f9)→`/u/` — the right vowel without the `/j/` onset, which Phase 5 adds by
  expanding `я`→`й+а` and `ю`→`й+у` before letter-to-sound.
- **`ь`** (soft sign) is silent on a control byte; palatalisation is Phase 5.

The clean fix for all three is the G2P/normalisation layer (Phase 5), not more
byte juggling. Phase 6 (the stress dictionary) likewise depends on Phase 5: a
dictionary entry carries stress as the combining-acute character `0xE2`, which
only takes effect once the G2P layer reads it.

### Phase 4: RHVoice Phonemes & Formant Locus Rules
- [ ] Map RHVoice phoneme inventory (6 monophthongs, iotated vowels, hard/soft consonants, affricates) into `ukua.statements` and `ukua.settings`.
- [ ] Implement formant loci in `lang/ukua/rules/is_val.up` (F1, F2, F3 frequencies, bandwidths, transitions).
- [ ] Implement G2P rules in `rules/` for digraphs (`дж`, `дз`), soft sign `ь` palatalization, and iotated vowels.

> Status (2026-09-25, after the expanded-audit ground truth): much of the
> intent is already met by the chassis and needs no new work. The digraphs
> render correctly by adjacency alone — `джерело`→`[.0dZE.0rE.1lo]` (`дж`→d+Z
> /dʒ/), `дзвін`→`[.1dzvin]` (`дз`→d+z) — so no digraph rule is required. The
> affricates and hushing consonants map cleanly: `ц`→T /ts/, `ч`→C (soft,
> adequate), `ш`→S, `ж`→Z, `щ`→S+C /ʃtʃ/. `г` and `х` both take /x/ ("A"), the
> best phone the inventory offers.
>
> The remaining vowel/consonant refinements — `о` /ɔ/ (open-o), `и` /ɪ/, `г` /ɦ/,
> a hard `ч` — are all **blocked on the same thing: there is no acoustic oracle
> for Ukrainian.** The phoneme audit is the only signal CI gives, and it is blind
> to formant nuance. Retargeting `о` from the close /o/ (0x20) to the open-o
> (0x21) that `pol_ph_on` uses was tried (commit d8fdc6a) and the phoneme line was
> byte-identical before and after — `гора`→`[.0Ao.1ra]`, `моя`→`[.0mo.1a]` either
> way — so the audit cannot confirm the change did anything, and it was reverted
> to keep the checkpoint fully proven. `и` /ɪ/, `г` /ɦ/ and a hard `ч` additionally
> need a *new* phoneme added to the synthesis inventory. This whole phase waits on
> a way to verify audio (wav samples / matrix baselines), not on the mappings.
> `ь` palatalisation and the `я/ю` glide belong to Phase 5, not here.

### Phase 5: Dictionary Ingestion from `lang-uk` Stress Dictionary
- [ ] Cloud CI workflow to fetch `lang-uk/ukrainian-word-stress-dictionary`.
- [ ] Compile base vocabulary into `ukua.dict` and `ukua.sets` using `tools/module/dict.py`.

### Phase 6: GitHub Actions CI & Verification
- [ ] Update `.github/workflows/build.yml` with `ukua` build steps and artifact uploads.
- [ ] Test sample phrases: `"Привіт"`, `"Добрий день"`, `"Слава Україні"`, `"п'ять"`, `"м'ясо"`.
- [ ] Verify audio generation and test matrix.

## How to Resume If Paused

1. Check git history: `git log -n 5 --oneline` to see the last completed step.
2. Check this progress file: see which checkbox in the roadmap is currently active.
3. Check build state: run `make LANG=lang/ukua probe` (or push branch to test on GitHub CI).
