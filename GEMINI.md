You are an expert database automation developer and backend engineer working on the "Local Video Server" project. The user's gallery groups are missing or unlinked due to a structural database refresh. We need a standalone automation script (`scripts/auto_grouper.py`) to scan the video collection, automatically group files by hair color keywords parsed from the filenames, and automatically route any motion formats (`.gif`, `.webp`) into a specialized "Motion" group.

### 1. TARGET TABLES & SCHEMA SCHEDULING
The script must interact directly with the authoritative database path `./data/video_metadata.db` using these explicit tables:
- `videos`: To query the authoritative list of active `filename` strings.
- `gallery_groups`: To create or locate the groups. Columns typically include: `id` (INTEGER PK), `name` (TEXT UNIQUE), and optional metadata fields like `cover_path`.
- `gallery_group_items`: To bind files to their respective groups. Columns include: `group_id` (INTEGER) and `image_path` (TEXT—which stores the video filename in this schema configuration).

### 2. TASK: CONSTRUCT THE AUTOMATED GALLERY GROUPER
Generate a clean, self-contained Python script saved at `scripts/auto_grouper.py`. The script must execute the following automated steps natively:

#### Phase A: Define Group Targets & Rules
1. **Motion Rule:** Any file ending with a `.gif` or `.webp` extension must immediately be assigned to a group named `Motion`, bypassing the hair color classification.
2. **Hair Color Classification Mapping:** For all other media files, check the `filename` case-insensitively against specific word variations to assign a category:
   - Keyword mappings for `Blonde`: matches `blonde`, `blond`
   - Keyword mappings for `Brunette`: matches `brunette`
   - Keyword mappings for `Redhead`: matches `redhead`, `red hair`, `ginger`
   - Keyword mappings for `Dark Hair`: matches `dark hair`, `black hair`, `raven`

#### Phase B: Execute Database Transaction Loops
1. Open a secure connection to `./data/video_metadata.db`.
2. **Upsert Groups:** For each target group (`Motion`, `Blonde`, `Brunette`, `Redhead`, `Dark Hair`), verify it exists in `gallery_groups` using `INSERT OR IGNORE`. Retrieve its matching `id`.
3. **Map Items:** Query all records from the `videos` table. Apply the rules from Phase A.
4. **Batch Insertion:** Run a high-performance batch insert (`executemany`) into `gallery_group_items` to map the items to their `group_id`. Use `INSERT OR IGNORE` to prevent uniqueness constraint faults if any structural items already exist in the background.

#### Phase C: Output & Summary Status
Print structured summary metrics to standard output tracking exactly how many files were successfully routed into each respective group gallery.

### 3. WINDOWS-SAFE POWERSHELL RUN & VERIFY PROTOCOL
Provide a single, flattened block of PowerShell commands optimized for Windows environments. It must:
- Execute `scripts/auto_grouper.py` inside the active `video-server` Docker container.
- Restart the `video-server` service container to instantly invalidate old in-memory representations and refresh the layout.
- Run a single-line inline Python check to query `gallery_group_items` along with an inner join on `gallery_groups`, printing out the count of active rows per group to verify structural synchronization.