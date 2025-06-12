# pyinstaller --onefile --icon=../logo.ico --windowed MMleo.py

import subprocess

mfa_path = r"MFAAvalonia.exe"

subprocess.run(mfa_path)