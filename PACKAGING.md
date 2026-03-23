# Packaging BioLitGraph

BioLitGraph now includes a desktop launcher that starts a local Waitress server and opens your browser automatically.

## Windows (.exe)

```bat
cd path	o\BioLitGraph
build_windows.bat
```

Your app will be created at:

```text
dist\BioLitGraph\BioLitGraph.exe
```

## macOS (.app)

```bash
cd /path/to/BioLitGraph
chmod +x build_macos.sh
./build_macos.sh
```

Your app will be created at:

```text
dist/BioLitGraph.app
```

## Notes

- Build Windows on Windows and macOS on a Mac.
- Packaged run outputs are saved to a user-writable location:
  - Windows: `%LOCALAPPDATA%\BioLitGraph`
  - macOS: `~/Library/Application Support/BioLitGraph`
  - Linux: `~/.local/share/BioLitGraph`
- The packaged app uses Waitress instead of the Flask development server.
