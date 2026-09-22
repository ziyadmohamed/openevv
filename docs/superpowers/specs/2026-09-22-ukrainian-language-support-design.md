# Ukrainian Language Support Architecture and Design

## Goal

Add native Ukrainian (`ukua`) language support to OpenEVV, expanding the engine's multi-language capacity, implementing full Cyrillic UTF-8 input handling, integrating phoneme definitions and pronunciation rules derived from RHVoice, incorporating the 2.9+ million word stress dictionary from `lang-uk/ukrainian-word-stress-dictionary`, and leveraging GitHub Actions CI for all heavy compilation, dataset fetching, and artifact generation.

## Background and Decisions

OpenEVV currently supports 10 languages (9 from IBM plus Polish `lang/plpl`).

Based on user requirements:
- **No eSpeak NG**: All phoneme definitions and letter-to-sound (G2P) logic are derived from **RHVoice** Ukrainian phonetic models.
- **Stress & Lexicon**: The primary lexicon and word stress data comes from **`lang-uk/ukrainian-word-stress-dictionary`** (over 2.9 million word forms with explicit combining acute accent `\u0301` markings).
- **Cloud-First Compilation (GitHub Actions CI)**: Due to local internet bandwidth constraints, dataset downloads (like the 2.9M word stress dictionary), rule compilation, and binary builds (`probe.exe`, `eci.dll`, audio samples) are executed on GitHub Actions runners, producing downloadable artifacts.
- **Comprehensive Commit & Progress Tracking**: Every single step is committed to git, accompanied by detailed progress documentation files so anyone can inspect or resume progress at any time.

## Engine Architecture Changes

### Multi-Language Family Expansion

The ECI runtime allocates fixed tables indexed by language family (`0..FAMILIES-1`). IBM used families 0 to 5 and 8, while reserving 6, 10, 11, and 16 for romanizers. Polish occupied family 17 (`0x110000`).

To support Ukrainian and future languages without running out of slots:
- Increase `FAMILIES`, `DICT_FAMILIES`, `RM_FAMILIES`, and `ROM_FAMILIES` from 18 (`0x12`) to 32 (`0x20`) across:
  - `src/eci/bridge/eci_statics.c`
  - `src/eci/dict/eci_dict.c`
  - `src/eci/lang/eci_romanizer.c`
  - `src/eci/lang/eci_romedll.c`
  - `src/eci/lang/eci_voicetable.c`
- Assign Ukrainian:
  - Language Tag: `ukua`
  - Display Name: `Ukrainian` in `tools/module/gather.py`
  - Family: `18` (`0x12`)
  - Dialect: `0`
  - ECI Language ID: `0x120000`
  - Settings Section: `[18.0]`, Path `eciukua.syn`, Library `Static Engine UKR`

## Language Module Structure (`lang/ukua`)

The Ukrainian module is derived from the Slavic chassis of Polish (`lang/plpl`), retaining its palatalization structures and single-byte UTF-8 conversion framework.

### 1. Cyrillic Alphabet and Codepoint Pipeline

The Delta virtual machine operates on single bytes (0x00 to 0xFF). Incoming Ukrainian UTF-8 text is converted transparently in `addTextRun` (`src/eci/synth/eci_synthtext.c`) using a translation table generated from `lang/ukua/ukua.codepoints`.

- **Alphabet Coverage (33 Letters, 66 Forms):**
  - Lowercase: `а, б, в, г, ґ, д, е, є, ж, з, и, і, ї, й, к, л, м, н, о, п, р, с, т, у, ф, х, ц, ч, ш, щ, ь, ю, я`
  - Uppercase: `А, Б, В, Г, Ґ, Д, Е, Є, Ж, З, И, І, Ї, Й, К, Л, М, Н, О, П, Р, С, Т, У, Ф, Х, Ц, Ч, Ш, Щ, Ь, Ю, Я`
  - Orthographic modifiers: Ukrainian apostrophe `ʼ` (U+02BC / U+2019 / U+0027) and hyphen `-`.
  - Stress accent modifier: Combining acute accent `\u0301` (U+0301) handled during preprocessing/recoding.
- **Codepoint Mapping (`ukua.codepoints`):**
  - Maps Unicode Cyrillic codepoints (U+0400 to U+045F and related) into allocated bytes in the range `0x80` to `0xE0`.
  - Compiled via `make EVVLANG=lang/ukua codepoints` to emit `delta_codepoints_ukua.c`.
- **Statement Table (`ukua.statements`):**
  - Managed via `tools/module/alphabet.py`.
  - Classifies each Cyrillic character by case, character type (letter/punct), phonetic class (vowel, consonant, glide), and individual fallback phoneme.

### 2. Phoneme Inventory and Formant Synthesis (RHVoice Model)

Ukrainian phonemes are modeled following RHVoice's Ukrainian phonetics mapped to Eloquence Klatt cascade synthesis formant targets:

- **Monophthong Vowels (6):**
  - `/a/` (`a`): F1 ~750 Hz, F2 ~1250 Hz, F3 ~2400 Hz
  - `/ɛ/` (`e` / `E`): F1 ~550 Hz, F2 ~1750 Hz, F3 ~2450 Hz
  - `/ɪ/` (`I` / Ukrainian `и`): F1 ~400 Hz, F2 ~1900 Hz, F3 ~2500 Hz
  - `/i/` (`i` / Ukrainian `і`): F1 ~270 Hz, F2 ~2200 Hz, F3 ~2800 Hz
  - `/ɔ/` (`o`): F1 ~500 Hz, F2 ~950 Hz, F3 ~2400 Hz
  - `/u/` (`u`): F1 ~300 Hz, F2 ~800 Hz, F3 ~2200 Hz
- **Iotated Vowels:**
  - `я` (`j'a`), `ю` (`j'u`), `є` (`j'e`), `ї` (`j'i`)
- **Consonants & Loci (`rules/is_val.up`):**
  - Labials (`b, p, v/w, m, f`): F2 locus ~850 Hz
  - Dentals/Alveolars (`d, t, z, s, n, l, r`): F2 locus ~1700 Hz
  - Velars (`g, k, x`): F2 locus ~1700-2400 Hz
  - Glottal/Pharyngeal (`h` / Ukrainian `г` / /ɦ/): voiced low-frequency fricative
  - Affricates (`ts` / `ц`, `dz` / `дз`, `tS` / `ч`, `dZ` / `дж`)
  - Retroflex/Postalveolar (`S` / `ш`, `Z` / `ж`, `StS` / `щ`): lower F3 ~2100-2200 Hz
  - Palatalized Dentals (`n^`, `l^`, `t^`, `d^`, `s^`, `z^`, `ts^`): elevated F2 ~2000-2400 Hz and F3 ~2600 Hz
- **Voice Configurations (`ukua.settings`):**
  - Defines the 8 standard Eloquence voice presets (Reed, Shelley, Bobby, Rocko, Glen, Sandy, Grandma, Junior) tuned for Ukrainian pitch ranges and speeds.

### 3. G2P Rules and Lexicon Pipeline

- **RHVoice G2P Rules (`lang/ukua/rules/`):**
  - Digraph expansion (`дж` -> `/dʒ/`, `дз` -> `/dz/`)
  - Palatalization trigger on soft sign `ь`
  - Iotated vowel decomposition: `j + vowel` at start of word, after vowel, or after apostrophe; palatalization of preceding consonant when following a consonant
  - Word-final devoicing and consonant cluster assimilation
- **Dictionary Compilation (`ukua.dict` and `ukua.sets`):**
  - Sourced from `lang-uk/ukrainian-word-stress-dictionary` (`stress.txt` containing 2.9M entries).
  - A cloud CI compilation step extracts the high-frequency and baseline vocabulary into `ukua.dict` and generates `ukua.sets` via `tools/module/dict.py`.

## GitHub Actions CI and Cloud Compilation

To address local bandwidth and computational limits:
- **CI Workflow Updates (`.github/workflows/build.yml`):**
  - Fetch `lang-uk/ukrainian-word-stress-dictionary` and RHVoice data in the CI runner.
  - Compile `ukua` in bytecode and C modes:
    `make -j"$(nproc)" RULES=c EVVPLAIN=1 LANGS="lang/enus lang/plpl lang/ukua" so all`
  - Run standalone Ukrainian probe checks:
    `make -j"$(nproc)" LANG=lang/ukua probe`
  - Package and upload build output artifacts (Linux shared library `libeci.so`, Windows binaries `probe.exe`, `eci.dll`, test audio samples) to GitHub Actions Artifacts for download.

## Progress Tracking and Documentation

- Maintain an ongoing, detailed progress log at `docs/progress/ukua-progress.md` with:
  - Completed steps, current status, and exact commands.
  - File changes and their rationale.
  - Instructions for resuming or verifying from any state.
- Strict git commit discipline: every milestone, refactor, and step is committed individually with clear messages.

## Verification and Testing Plan

1. **Unit Compilation Verification:**
   - Verify `FAMILIES` expansion compiles cleanly without regressions across all existing 10 languages.
   - Verify `lang/ukua` tables (`ukua.globals`, `ukua.settings`, `ukua.statements`, `ukua.sets`, `ukua.consts`, `ukua.codepoints`) generate valid C code via `make LANG=lang/ukua tables-write`.
2. **Phonetic and Audio Verification:**
   - Verify `build/probe "привіт" out.wav p` outputs expected phoneme stream matching RHVoice.
   - Speak representative phrases:
     - Greetings: `"Добрий день"`, `"Привіт"`
     - Punctuation and apostrophe: `"п'ять"`, `"м'ясо"`
     - Palatalization: `"день"`, `"сіль"`, `"любов"`
     - Alphabet coverage.
3. **Regression Testing:**
   - Execute existing test suite: `test/hash.sh` and `make crashers` must remain 100% green.
