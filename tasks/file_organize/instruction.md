`/app/downloads/` is a mess of files. Organize it **in place**:

- Move images (`.jpg`, `.jpeg`, `.png`, `.gif`) into `/app/downloads/images/`
- Move documents (`.pdf`, `.docx`, `.txt`, `.md`) into `/app/downloads/docs/`
- Move archives (`.zip`, `.tar.gz`) into `/app/downloads/archives/`
- Everything else into `/app/downloads/other/`
- Extension matching must be case-insensitive (`photo.JPG` is an image).
- Delete any file whose size is 0 bytes instead of moving it.
- Write `/app/downloads/MANIFEST.txt` listing every moved file as `<folder>/<filename>`, sorted, one per line.
