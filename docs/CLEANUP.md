# Development disk cleanup

`max clean` is a core command on macOS and Linux; no module needs enabling.
It previews regenerable development caches without changing files or MaxCLI
configuration. Use `max-dev` for these examples when testing a local checkout.

```sh
max clean                             # Preview known development caches
max clean --all                       # Also measure larger folders for manual review
max clean --category xcode --category gradle
max clean --category npm --dry-run --json
max clean --category xcode --apply     # Show the plan and ask for confirmation
max --non-interactive clean --category npm --apply --yes --json
```

Without `--category`, all supported cache categories are selected. Repeat the
flag to select several. `--dry-run` explicitly selects the default preview mode
and cannot be combined with `--apply`. `--yes` only works with `--apply`; it
approves permanent removal without a prompt. JSON application also requires
`--yes`, so stdout remains a single JSON report.

Stop builds, package installs, Gradle daemons, Xcode, simulators, and test browsers
that use the selected caches before applying cleanup. The command removes cache
contents permanently and preserves the cache root directories. Subsequent
installs may require network access, and builds and indexing may take longer.
Test browser binaries need reinstalling before their next use.

## Cache categories

All paths below are relative to your home directory. Only these default
locations are eligible for removal. Custom locations set in environment
variables or tool configuration are not discovered or removed.

| Category | macOS locations | What happens after removal |
| --- | --- | --- |
| `npm` | `.npm/_cacache` | Packages are downloaded again. npm configuration, logs, and global installations remain. |
| `bun` | `.bun/install/cache` | Packages are downloaded again. Bun itself and installed project dependencies remain. |
| `pnpm` | `Library/Caches/pnpm` | Metadata and temporary `dlx` installations are recreated. The shared package store remains. |
| `gradle` | `.gradle/caches`, `.gradle/wrapper/dists` | Dependencies, build caches, and Gradle distributions are recreated. Properties, init scripts, and toolchain JDKs remain. |
| `cocoapods` | `Library/Caches/CocoaPods` | Pods are downloaded again. Project `Pods` directories and spec repositories remain. |
| `xcode` | `Library/Developer/Xcode/DerivedData`, `Library/Caches/com.apple.dt.Xcode` | Builds and indexing run again. Archives, device support, and signing settings remain. |
| `simulator-caches` | `Library/Developer/CoreSimulator/Caches` | User simulator caches are recreated. Devices, their data, and runtimes remain. |
| `test-browsers` | `Library/Caches/ms-playwright`, `.cache/puppeteer` | Run the appropriate Playwright or Puppeteer browser installation again. |

On Linux, `npm`, `bun`, `gradle`, and Puppeteer use the same relative paths.
pnpm uses `.cache/pnpm` and Playwright uses `.cache/ms-playwright`. The macOS-only
categories have no targets on Linux. Other operating systems are unsupported.

## Larger data folders

`--all` adds measurements and manual-review guidance for the default shared pnpm
store, Android virtual devices and SDK, and, on macOS, Library caches,
application support data, simulator devices, runtime disk images, Xcode device
support, and archives. These folders remain untouched even with `--apply --yes`.
Simulator runtime images are inspected at `/Library/Developer/CoreSimulator/Images`;
mounted runtime volumes are not traversed. This does not cover every runtime
location used by every Xcode version.

The broader folders can overlap with individual cache measurements. For example,
`Library/Caches` includes CocoaPods and Xcode caches. There is no combined total
for review-only folders, and they do not contribute to the reclaim estimate.
The scan is not a breakdown of macOS System Data. It does not scan repositories,
remove `node_modules`, clear browser profiles, or manage Docker resources.
Use `max docker clean` separately for Docker.

For the shared package store, [pnpm's native `store prune`](https://pnpm.io/cli/store)
removes unreferenced packages. Run `pnpm store path` to check the configured store
before pruning, especially when using multiple disks or pnpm versions.
Use [Xcode's runtime management](https://developer.apple.com/documentation/safari-developer-tools/adding-additional-simulators)
to remove unused simulator runtimes, and Android Studio's SDK and Device Managers
to remove unused SDK components and virtual devices.

## Estimates, failures, and scripting

Sizes count allocated regular-file blocks, skip symlink destinations, and count
each inode once within a target. Hard-linked files are excluded from reclaim
estimates because other links may keep their storage allocated. APFS clones,
snapshots, running tools, and filesystem accounting can further reduce actual
savings. `removed_allocated_bytes` measures the reduction in scanned cache file
allocation; it is not a measurement of newly available disk space.

Symlinks in cache contents are unlinked when applying, without deleting their
destinations. A symlink in a target's path, unreadable files, special files, or
nested filesystems on another device make the scan incomplete. Cleanup refuses
the complete selected set if any selected cache cannot be fully inspected.
Select narrower categories or resolve the reported errors before retrying.
Directory identity is rechecked after confirmation. All traversal and deletion
use directory descriptors without following symlinks.

JSON reports include `applied`, `ok`, `estimated_reclaimable_bytes`,
`removed_allocated_bytes`, and `targets`. Each target includes its category, path,
effect, `cleanable`, `status` (`ready`, `missing`, or `error`), allocated bytes,
estimated reclaimable bytes, and errors. Applied targets also include
`cleanup_status` and, when verification succeeds, remaining and removed allocated
bytes. Missing cache directories are normal and are not created.

Exit status is 0 for a complete preview or successful application, 1 for errors
or cancellation, and 130 for interruption. A failure during deletion may leave
some selected contents removed; consult the per-target result before retrying.
Review-only scan errors produce a nonzero result but do not prevent cleanup of
fully inspected cache categories.
