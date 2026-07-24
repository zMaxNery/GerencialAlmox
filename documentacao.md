### Comando para compilar corretamente o projeto
rm dist -r
pyinstaller --onedir --windowed --name="GerencialAlmox" --hidden-import core.almox_repository --hidden-import core.supabase_client --hidden-import dotenv --collect-all=supabase --collect-all=extract_msg --collect-submodules=bs4 --collect-all=lxml --collect-all=tkinterdnd2 --collect-submodules=win32com --hidden-import=pythoncom --hidden-import=pywintypes main.py
rm build -r
rm GerencialAlmox.spec