# Ukrainian Language Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add native Ukrainian (`ukua`) language support to OpenEVV, expanding engine capacity, implementing Cyrillic UTF-8 input recoding, integrating RHVoice phonemes and G2P rules, incorporating word stress from `lang-uk/ukrainian-word-stress-dictionary`, and configuring GitHub Actions CI for cloud compilation and artifact delivery.

**Architecture:** Expand engine `FAMILIES` table limit to 32, create `lang/ukua` chassis based on Polish (`lang/plpl`), configure `ukua.codepoints` for 33 Ukrainian Cyrillic letters plus apostrophe, map RHVoice phonetic definitions to Klatt cascade formant loci, author Delta G2P rules in `rules/`, build dictionary compiler for `lang-uk` stress dictionary, and automate builds and artifact distribution via GitHub Actions CI.

**Tech Stack:** C (C99/C11), Python 3, Make, Delta VM assembler (`.dr` / `.up`), GitHub Actions CI.

**Spec:** `docs/superpowers/specs/2026-09-22-ukrainian-language-support-design.md`

## Global Constraints

- No external runtime dependencies in OpenEVV core binaries (`probe`, `eci.dll`).
- Existing 10 languages must suffer zero regression (all existing tests in `test/hash.sh` and `make crashers` must pass).
- Strictly follow Markdown formatting rules: no mid-paragraph hard line wraps.
- Commit after every task and keep `docs/progress/ukua-progress.md` updated.
- Heavy compilation, large dictionary downloads, and artifact releases must be supported via GitHub Actions CI.

---

### Task 1: Engine Multi-Language Scalability (`FAMILIES` Expansion)

**Files:**
- Modify: `src/eci/bridge/eci_statics.c:14`
- Modify: `src/eci/dict/eci_dict.c:47`
- Modify: `src/eci/lang/eci_romanizer.c:92`
- Modify: `src/eci/lang/eci_romedll.c:23`
- Modify: `src/eci/lang/eci_voicetable.c:38`
- Modify: `tools/module/gather.py:47-49`
- Modify: `docs/progress/ukua-progress.md`

**Interfaces:**
- Consumes: ECI language constants and family indexing.
- Produces: Capacity for 32 families (`0x00`..`0x1F`), with Family 18 (`0x120000`) allocated to `ukua`.

- [ ] **Step 1: Expand FAMILIES to 32 in engine source files**

In `src/eci/bridge/eci_statics.c`:
Change `#define FAMILIES 18` to `#define FAMILIES 32`.

In `src/eci/dict/eci_dict.c`:
Change `#define DICT_FAMILIES 0x12` to `#define DICT_FAMILIES 0x20`.

In `src/eci/lang/eci_romanizer.c`:
Change `#define RM_FAMILIES 0x12` to `#define RM_FAMILIES 0x20`.

In `src/eci/lang/eci_romedll.c`:
Change `#define ROM_FAMILIES 0x12` to `#define ROM_FAMILIES 0x20`.

In `src/eci/lang/eci_voicetable.c`:
Change `#define FAMILIES 18` to `#define FAMILIES 32`.

- [ ] **Step 2: Register ukua in tools/module/gather.py**

Add `"ukua": "Ukrainian"` under `NAMES` in `tools/module/gather.py`.

- [ ] **Step 3: Verify existing table checks and regression tests**

Run:
```bash
python3 tools/module/gather.py plpl
make tables-check
```
Verify zero regressions on existing 10 languages.

- [ ] **Step 4: Update progress log and commit**

Update `docs/progress/ukua-progress.md` checking off Phase 1.
Commit:
```bash
git add src/eci/ tools/module/gather.py docs/progress/ukua-progress.md
git commit -m "feat(core): expand ECI engine language family capacity to 32 and register ukua"
```

---

### Task 2: Ukrainian Module Initial Chassis Setup (`lang/ukua`)

**Files:**
- Create: `lang/ukua/ukua.globals`
- Create: `lang/ukua/ukua.settings`
- Create: `lang/ukua/ukua.statements`
- Create: `lang/ukua/ukua.sets`
- Create: `lang/ukua/ukua.consts`
- Create: `lang/ukua/ukua.dict`
- Create: `lang/ukua/rules/` (copied from `lang/plpl/rules/`)
- Modify: `docs/progress/ukua-progress.md`

**Interfaces:**
- Consumes: Polish (`lang/plpl`) text forms and Delta compiler scripts.
- Produces: Compilable `lang/ukua` module skeleton registered as Language ID `0x120000` (Family 18, Dialect 0).

- [ ] **Step 1: Fork lang/plpl text forms to lang/ukua**

Create `lang/ukua` and copy the text files and `rules/` from `lang/plpl/`:
- `plpl.globals` -> `ukua.globals`
- `plpl.settings` -> `ukua.settings`
- `plpl.statements` -> `ukua.statements`
- `plpl.sets` -> `ukua.sets`
- `plpl.consts` -> `ukua.consts`
- `plpl.dict` -> `ukua.dict`
- `rules/` -> `lang/ukua/rules/`

- [ ] **Step 2: Update ukua.settings for Family 18**

Update `lang/ukua/ukua.settings`:
- Set library name: `library Static Engine UKR`
- Set section header: `\n\n\n\n[18.0]`
- Set path: `Path=eciukua.syn`

- [ ] **Step 3: Generate C source files for ukua**

Run:
```bash
python3 tools/module/gather.py ukua
make LANG=lang/ukua tables-write
```
Verify `delta_lang_ukua.c`, `delta_globals_ukua.c`, `delta_link_ukua.c`, etc. are generated.

- [ ] **Step 4: Verify initial chassis compiles**

Run:
```bash
make LANG=lang/ukua rulecode
```
Verify that `delta_rules_ukua.c` and its header are generated cleanly without errors.

- [ ] **Step 5: Update progress log and commit**

Update `docs/progress/ukua-progress.md` checking off Phase 2.
Commit:
```bash
git add lang/ukua/ docs/progress/ukua-progress.md
git commit -m "feat(ukua): initialize Ukrainian language module chassis from Slavic plpl base"
```

---

### Task 3: Cyrillic Alphabet & UTF-8 Codepoints Pipeline

**Files:**
- Create: `lang/ukua/ukua.codepoints`
- Modify: `lang/ukua/ukua.statements`
- Generate: `lang/ukua/delta_codepoints_ukua.c`
- Modify: `docs/progress/ukua-progress.md`

**Interfaces:**
- Consumes: Unicode UTF-8 Cyrillic character sequences (`U+0400`..`U+04FF`, apostrophe `U+02BC` / `U+2019` / `U+0027`, combining acute accent `U+0301`).
- Produces: Single-byte translation table in `delta_codepoints_ukua.c` consumed by `addTextRun` in `src/eci/synth/eci_synthtext.c`.

- [ ] **Step 1: Define Ukrainian Cyrillic codepoint map in ukua.codepoints**

Create `lang/ukua/ukua.codepoints` mapping each Ukrainian Cyrillic letter to a distinct single byte in the free range `0x80`..`0xDF`:
- Lowercase:
  - `а`: `0430 80`
  - `б`: `0431 81`
  - `в`: `0432 82`
  - `г`: `0433 83`
  - `ґ`: `0491 84`
  - `д`: `0434 85`
  - `е`: `0435 86`
  - `є`: `0454 87`
  - `ж`: `0436 88`
  - `з`: `0437 89`
  - `и`: `0438 8a`
  - `і`: `0456 8b`
  - `ї`: `0457 8c`
  - `й`: `0439 8d`
  - `к`: `043a 8e`
  - `л`: `043b 8f`
  - `м`: `043c 90`
  - `н`: `043d 91`
  - `о`: `043e 92`
  - `п`: `043f 93`
  - `р`: `0440 94`
  - `с`: `0441 95`
  - `т`: `0442 96`
  - `у`: `0443 97`
  - `ф`: `0444 98`
  - `х`: `0445 99`
  - `ц`: `0446 9a`
  - `ч`: `0447 9b`
  - `ш`: `0448 9c`
  - `щ`: `0449 9d`
  - `ь`: `044c 9e`
  - `ю`: `044e 9f`
  - `я`: `044f a0`
- Uppercase:
  - `А`..`Я`: `a1`..`c1`
- Apostrophe:
  - `02bc c2` (modifier letter apostrophe)
  - `2019 c2` (right single quotation mark)
  - `0027 c2` (ascii apostrophe)
- Combining acute accent (stress):
  - `0301 c3`

- [ ] **Step 2: Compile delta_codepoints_ukua.c**

Run:
```bash
make EVVLANG=lang/ukua codepoints
```
Verify `lang/ukua/delta_codepoints_ukua.c` is generated with the codepoint lookup table.

- [ ] **Step 3: Register Cyrillic character properties in ukua.statements**

Use `tools/module/alphabet.py` to populate properties for each code:
- Vowels: `а, е, и, і, о, у` (type=letter, letter=vow)
- Consonants: `б, в, г, ґ, д, ж, з, к, л, м, н, п, р, с, т, ф, х, ц, ч, ш, щ` (type=letter, letter=cons)
- Glides: `й` (type=letter, letter=glide)
- Soft sign: `ь` (type=letter, letter=cons)
- Apostrophe: `c2` (type=punct)

- [ ] **Step 4: Update progress log and commit**

Update `docs/progress/ukua-progress.md` checking off Phase 3.
Commit:
```bash
git add lang/ukua/ukua.codepoints lang/ukua/delta_codepoints_ukua.c lang/ukua/ukua.statements docs/progress/ukua-progress.md
git commit -m "feat(ukua): map Cyrillic alphabet, apostrophe, and stress mark into UTF-8 codepoints pipeline"
```

---

### Task 4: RHVoice Phoneme Inventory & Klatt Formant Targets

**Files:**
- Modify: `lang/ukua/ukua.settings`
- Modify: `lang/ukua/ukua.statements`
- Modify: `lang/ukua/rules/is_val.up`
- Modify: `docs/progress/ukua-progress.md`

**Interfaces:**
- Consumes: RHVoice Ukrainian phonetic definitions (6 monophthongs, iotated vowels, palatalized series, fricative /ɦ/).
- Produces: Klatt synthesizer formant locus targets in `is_val.up` and phoneme duration/energy presets in `ukua.settings`.

- [ ] **Step 1: Configure Ukrainian phoneme inventory in ukua.settings**

Set phoneme parameter lines in `ukua.settings`:
- Monophthong vowels: `a, e, i, I, o, u`
- Consonants: `b, d, g, p, t, k, v, f, z, s, Z, S, h, x, m, n, l, r, j`
- Affricates: `ts, dz, tS, dZ`
- Palatalized series: `n^, l^, t^, d^, s^, z^, ts^`

- [ ] **Step 2: Implement formant locus rules in lang/ukua/rules/is_val.up**

Author Ukrainian formant targets in `lang/ukua/rules/is_val.up`:
- `/ɦ/` (Ukrainian `г`): low F1 ~350 Hz, F2 ~1300 Hz voiced glottal locus.
- Retroflex / Postalveolar (`ш`, `ж`, `ч`): low F3 ~2100-2200 Hz.
- Palatalized consonants: high F2 ~2100-2400 Hz, F3 ~2600 Hz.
- Ukrainian vowel targets:
  - `/ɪ/` (`I`): F1 400 Hz, F2 1900 Hz, F3 2500 Hz.
  - `/i/` (`i`): F1 270 Hz, F2 2200 Hz, F3 2800 Hz.
  - `/a/`: F1 750 Hz, F2 1250 Hz, F3 2400 Hz.
  - `/ɛ/` (`e`): F1 550 Hz, F2 1750 Hz, F3 2450 Hz.
  - `/ɔ/` (`o`): F1 500 Hz, F2 950 Hz, F3 2400 Hz.
  - `/u/`: F1 300 Hz, F2 800 Hz, F3 2200 Hz.

- [ ] **Step 3: Compile rules and verify bytecode/C generation**

Run:
```bash
make LANG=lang/ukua rulecode
make LANG=lang/ukua tables-write
```
Verify clean compilation of `delta_rules_ukua.c`.

- [ ] **Step 4: Update progress log and commit**

Update `docs/progress/ukua-progress.md` checking off Phase 4.
Commit:
```bash
git add lang/ukua/ukua.settings lang/ukua/rules/is_val.up docs/progress/ukua-progress.md
git commit -m "feat(ukua): map RHVoice phoneme inventory and implement Klatt formant locus rules"
```

---

### Task 5: G2P Rules (Letter-to-Sound, Digraphs & Palatalization)

**Files:**
- Create: `lang/ukua/rules/uk_l2s.up`
- Modify: `lang/ukua/rules/`
- Modify: `docs/progress/ukua-progress.md`

**Interfaces:**
- Consumes: Cyrillic character tokens arriving from `addTextRun`.
- Produces: Resolved phoneme token sequences with palatalization and stress applied.

- [ ] **Step 1: Author letter-to-sound rules in uk_l2s.up**

Implement G2P transformation rules in `lang/ukua/rules/uk_l2s.up`:
- Digraph rules:
  - `д` followed by `ж` -> phoneme `dZ` (дж)
  - `д` followed by `з` -> phoneme `dz` (дз)
- Palatalization rules:
  - Dental consonants (`д, т, з, с, ц, л, н`) followed by `ь` -> palatalized phonemes (`d^, t^, z^, s^, ts^, l^, n^`) and consume `ь`.
- Iotated vowel rules:
  - `я, ю, є, ї`:
    - After vowel, apostrophe, or start of word: emit `j` + vowel (`a, u, e, i`).
    - After consonant: palatalize preceding consonant and emit vowel (`a, u, e, i`).
- Apostrophe rule:
  - Consumes apostrophe `c2` while preventing palatalization of preceding consonant.

- [ ] **Step 2: Recompile rule code**

Run:
```bash
make LANG=lang/ukua rulecode
```
Verify that upper-form compiler processes `uk_l2s.up` cleanly.

- [ ] **Step 3: Verify phoneme generation**

Test phoneme output for basic Ukrainian words:
- `"день"` -> expects `d'e.n^`
- `"м'ясо"` -> expects `m.j'a.s.o`
- `"п'ять"` -> expects `p.j'a.t^`

- [ ] **Step 4: Update progress log and commit**

Update `docs/progress/ukua-progress.md` checking off Phase 5.
Commit:
```bash
git add lang/ukua/rules/ docs/progress/ukua-progress.md
git commit -m "feat(ukua): implement Ukrainian G2P rules for digraphs, palatalization, and iotated vowels"
```

---

### Task 6: Lexicon Ingestion from `lang-uk/ukrainian-word-stress-dictionary`

**Files:**
- Create: `tools/module/ukua_dict.py`
- Modify: `lang/ukua/ukua.dict`
- Generate: `lang/ukua/ukua.sets`
- Modify: `docs/progress/ukua-progress.md`

**Interfaces:**
- Consumes: Word entries from `lang-uk/ukrainian-word-stress-dictionary` (`stress.txt` format with `\u0301`).
- Produces: Formatted `ukua.dict` entries and compiled Delta lookup sets `ukua.sets`.

- [ ] **Step 1: Write dictionary ingestion script tools/module/ukua_dict.py**

Author `tools/module/ukua_dict.py`:
- Parses words with combining acute accent `\u0301`.
- Identifies stressed syllable.
- Formats words into OpenEVV dictionary syntax.
- Filters high-frequency / core lexicon for initial base dictionary.

- [ ] **Step 2: Generate initial core dictionary ukua.dict**

Run `tools/module/ukua_dict.py` with core vocabulary (greetings, numerals, common pronouns, top 1,000 words).
Populate `lang/ukua/ukua.dict`.

- [ ] **Step 3: Compile dictionary sets**

Run:
```bash
python3 tools/module/dict.py write ukua
make LANG=lang/ukua tables-write
```
Verify `lang/ukua/ukua.sets` and `delta_sets_ukua.c` compile cleanly.

- [ ] **Step 4: Update progress log and commit**

Update `docs/progress/ukua-progress.md` checking off Phase 6.
Commit:
```bash
git add tools/module/ukua_dict.py lang/ukua/ukua.dict lang/ukua/ukua.sets docs/progress/ukua-progress.md
git commit -m "feat(ukua): add dictionary ingestion script and compile initial Ukrainian stress lexicon"
```

---

### Task 7: GitHub Actions CI Integration & Cloud Artifact Delivery

**Files:**
- Modify: `.github/workflows/build.yml`
- Modify: `docs/progress/ukua-progress.md`

**Interfaces:**
- Consumes: Push events to `main` and tagged releases `v*`.
- Produces: GitHub Actions CI build jobs that build `lang/ukua` in bytecode and C, run probe tests, and upload standalone binaries (`probe.exe`, `eci.dll`, audio samples) as workflow artifacts.

- [ ] **Step 1: Add ukua to GitHub Actions CI workflow**

In `.github/workflows/build.yml`:
- Add `lang/ukua` to the multi-language list in release and workflow dispatch runs:
  `langs=$(printf 'lang/%s ' enus engb dede eses esus frfr frca itit plpl jajp ukua)`
- Add standalone Ukrainian probe verification step:
  ```yaml
  - name: Check Ukrainian probe
    run: |
      make -j"$(nproc)" LANG=lang/ukua probe
      build/probe "Привіт" test-ukua.wav
  ```
- Add artifact upload step for Windows/Linux binaries and audio samples.

- [ ] **Step 2: Validate workflow syntax**

Verify `.github/workflows/build.yml` formatting and yaml syntax.

- [ ] **Step 3: Update progress guide and finalize roadmap**

Update `docs/progress/ukua-progress.md` with complete instructions on how GitHub Actions CI builds and publishes the artifacts.

- [ ] **Step 4: Commit and push**

Commit:
```bash
git add .github/workflows/build.yml docs/progress/ukua-progress.md
git commit -m "ci: add Ukrainian language build and artifact publishing to GitHub Actions workflow"
```
