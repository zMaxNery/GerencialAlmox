### Comando para compilar corretamente o projeto
powershell -ExecutionPolicy Bypass -File .\compilador.ps1

### Zerar dados do banco
begin;

truncate table
    public.baixas_resumo_totvs,
    public.ajustes_materiais_fabrica,
    public.consumos_materiais_fabrica,
    public.devolucoes_entrega,
    public.lotes_materiais_fabrica,
    public.apontamentos_entrega,
    public.itens_resumo_totvs,
    public.itens_requisicao,
    public.emails_importados
restart identity;

commit;