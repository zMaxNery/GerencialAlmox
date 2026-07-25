### Comando para compilar corretamente o projeto
rm dist -r
pyinstaller --onedir --windowed --name="GerencialAlmox" --hidden-import core.almox_repository --hidden-import core.supabase_client --hidden-import dotenv --collect-all=supabase --collect-all=extract_msg --collect-submodules=bs4 --collect-all=lxml --collect-all=tkinterdnd2 --collect-submodules=win32com --hidden-import=pythoncom --hidden-import=pywintypes main.py
rm build -r
rm GerencialAlmox.spec

### Zerar dados do banco
begin;

truncate table
    public.ajustes_materiais_fabrica,
    public.consumos_materiais_fabrica,
    public.devolucoes_entrega,
    public.lotes_materiais_fabrica,
    public.apontamentos_entrega,
    public.itens_resumo_totvs,
    public.itens_requisicao,
    public.importacoes_email
restart identity;

commit;
