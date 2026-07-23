### Comando para compilar corretamente o projeto
rm dist -r
pyinstaller --onedir --windowed --name="GerencialAlmox" --hidden-import core.almox_repository --hidden-import core.supabase_client --hidden-import dotenv --collect-all=supabase --collect-all=extract_msg --collect-submodules=bs4 --collect-all=lxml --hidden-import=windnd main.py
rm build -r
rm GerencialAlmox.spec