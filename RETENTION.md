# Replication retention and recovery

Use a new versioned archive for every reviewed source/artifact revision. Keep source Git bundles,
exact inputs, raw journals (including failures), analysis outputs, provenance, checksums and the
compiled paper together. Do not overwrite an earlier archive, silently merge generations, or
store the only copy under a worktree or temporary directory. The replication archive contains no
credentials. Future raw collection must retain dispatch/results in both durable journal sinks.

## Current protection layers

- Canonical study data and a full Linux research backup remain outside the source worktree.
- A sealed Linux version directory uses `0555` directories and `0444` files. An ordinary user
  cannot unlink its disposable sentinel or overwrite files without deliberately changing modes.
- Windows protected versions are under `C:\Users\Usuario\ResearchBackups\ProtectedPapers`.
  `scripts/protect_windows_paper_archive.ps1` copies into a **new** directory, verifies SHA256,
  denies current-user deletion/delete-child/write, and proves both denial boundaries using a
  disposable sentinel. Never test removal of an actual scientific archive. Owner/admin can
  deliberately change ACLs; this is accidental-deletion protection, not an immutable legal hold.
- User-authorized OneDrive versions are under
  `C:\Users\Usuario\OneDrive\ResearchBackups\sim-to-real`. Keep this sync directory writable;
  do not apply the protected-vault ACL there, which could obstruct synchronization.
  `scripts/check_onedrive_sync.ps1` records hashes and the Windows Cloud Files API IN_SYNC state.
  This is provider-client synchronization evidence, not an independently downloaded server hash.

Linux/Windows local directories reside on one physical SSD. OneDrive supplies the separate cloud
copy only after synchronization is confirmed. Copying into a OneDrive folder alone is insufficient.
The current account is personal: Microsoft documents a 30-day web recycle-bin recovery period
for ordinary deletions, not unlimited immutable retention. Manually emptying the recycle bin,
account loss, changing local permissions or deleting every copy is outside this protection claim.
See [Microsoft recovery guidance](https://support.microsoft.com/en-us/onedrive/restore-your-onedrive-files)
and [Cloud Files IN_SYNC definition](https://learn.microsoft.com/en-us/windows/win32/api/cfapi/ne-cfapi-cf_placeholder_state).

## Recover without calling a provider

1. Choose a protected version, or recover the version from the OneDrive **web** recycle bin.
2. Verify the archive SHA256 against its sidecar/retention receipt before extracting to a new path.
3. Run `sha256sum -c SHA256SUMS` from the extracted root.
4. Clone the included `SOURCE_FINAL.bundle` on the named branch and verify its full commit SHA.
5. Follow REPLICATION.md to reparse retained raw responses, compare report bytes and export assets.
   No API credential, new model generation or existing worktree is required.
6. Preserve the archive and recover into a new writable workspace; do not unseal/delete the backup.

The retained drill creates and deletes only an explicitly marked expendable working copy, restores
from the protected Windows archive, checks 132 file hashes and reproduces both original raw-replay
reports byte for byte. Its code, execution record and the later final-version checks accompany the
full-text audit bundle. Protected sentinels are intentionally retained as repeatable evidence.
No Google Cloud bucket was created; the user chose Windows OneDrive.
