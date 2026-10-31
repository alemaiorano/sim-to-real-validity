# Public history maintenance

Publication-only identities in historical text, filenames, messages and two generated PDFs
were generalized. Original refs, files and PDFs remain in private versioned backups. The current
manuscript/PDF, scientific reports, primary collector, estimators and raw inputs are unchanged.

History maintenance changes commit ancestry. PUBLIC_SOURCE_REVISIONS.json records archival and
public revision/tree identities. Historical GPT replay now resolves the archival source through
that map and verifies an identical complete producer tree before importing it. Output archive IDs
and numerical report bytes stay unchanged. The producer hash/provenance is updated explicitly.

Verification includes real Git revision/tree tests, offline GPT checkpoint replay, all report and
source pins, current clean-clone reproduction and scanning every reachable public branch commit,
path/blob/message and PDF. This does not claim deletion of provider-held PR refs or caches.
Original/source-after bundles and execution records remain protected and synchronized to OneDrive.
