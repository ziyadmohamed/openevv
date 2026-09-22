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
- [ ] Expand `FAMILIES`, `DICT_FAMILIES`, `RM_FAMILIES`, `ROM_FAMILIES` from 18 to 32 in core engine headers and C files.
- [ ] Register `ukua` in `tools/module/gather.py`.
- [ ] Verify zero regressions in existing 10 languages.

### Phase 2: Ukrainian Module Chassis Setup
- [ ] Fork `lang/plpl` chassis to `lang/ukua`.
- [ ] Rename symbols and file headers from `plpl` to `ukua`.
- [ ] Update `ukua.settings` for Language ID `[18.0]` and Ukrainian voice profiles.
- [ ] Update `ukua.globals` and statement references.

### Phase 3: Cyrillic Alphabet & UTF-8 Codepoints
- [ ] Define Ukrainian Cyrillic alphabet (33 lowercase, 33 uppercase, apostrophe, hyphen) in `ukua.statements`.
- [ ] Create `lang/ukua/ukua.codepoints` mapping Unicode Cyrillic (U+0400..U+04FF) to Delta byte codes (0x80..0xDF).
- [ ] Compile `delta_codepoints_ukua.c` and verify UTF-8 input recoding in `addTextRun`.

### Phase 4: RHVoice Phonemes & Formant Locus Rules
- [ ] Map RHVoice phoneme inventory (6 monophthongs, iotated vowels, hard/soft consonants, affricates) into `ukua.statements` and `ukua.settings`.
- [ ] Implement formant loci in `lang/ukua/rules/is_val.up` (F1, F2, F3 frequencies, bandwidths, transitions).
- [ ] Implement G2P rules in `rules/` for digraphs (`дж`, `дз`), soft sign `ь` palatalization, and iotated vowels.

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
