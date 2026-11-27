import os
import shutil
import time


def cleanup_old_jobs(max_age_seconds: int = 86400, keep_latest: int = 10) -> dict:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(base_dir, ".."))
    target_roots = [
        os.path.join(project_root, "logs", "jobs"),
        os.path.join(project_root, "uploads", "jobs"),
    ]

    now = time.time()
    removed_dirs = 0
    freed_bytes = 0

    for root in target_roots:
        if not os.path.isdir(root):
            continue

        entries = []
        for name in os.listdir(root):
            full_path = os.path.join(root, name)
            if os.path.isdir(full_path):
                try:
                    mtime = os.path.getmtime(full_path)
                except OSError:
                    mtime = now
                entries.append((mtime, full_path))

        # Newest first so we always keep the most recent jobs
        entries.sort(key=lambda item: item[0], reverse=True)

        for idx, (mtime, folder_path) in enumerate(entries):
            if idx < keep_latest:
                continue
            if (now - mtime) < max_age_seconds:
                continue

            dir_size = 0
            for dirpath, _, filenames in os.walk(folder_path):
                for fn in filenames:
                    fp = os.path.join(dirpath, fn)
                    try:
                        dir_size += os.path.getsize(fp)
                    except OSError:
                        pass

            try:
                shutil.rmtree(folder_path, ignore_errors=True)
                removed_dirs += 1
                freed_bytes += dir_size
            except Exception:
                pass

    return {
        "removed_dirs": removed_dirs,
        "freed_bytes": freed_bytes,
    }


if __name__ == "__main__":
    summary = cleanup_old_jobs()
    print(f"[CLEANUP] Removed {summary['removed_dirs']} stale job folders ({summary['freed_bytes']} bytes).")