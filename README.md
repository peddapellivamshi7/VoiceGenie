# AI Voice Assistant for Windows (Gemini)

This project is distributed as a Windows `.exe` installer.

## Build the installer EXE

Prerequisite: install **Inno Setup 6** (provides `ISCC.exe`).

From project folder:

```powershell
cd c:\Users\CR\College\COURSE\PYTHON\AI-Integrated-Personal-Voice-Assistant
.\build_installer_exe.ps1
```

Output:
- `dist\AI-Voice-Assistant-Installer.exe`

## End-user installation steps

1. Download `AI-Voice-Assistant-Installer.exe`
2. Run the installer
3. Installer copies files and runs dependency setup automatically
4. Edit `.env` and set `GEMINI_API_KEY`
5. Launch from desktop/start-menu shortcut

## Notes

- Platform: Windows 10/11
- Python 3.10+ is required on target laptop for dependency install
- If mic is wrong, set `MICROPHONE_INDEX` in `.env`
- Keep `STT_ENGINE=google` for best reliability
