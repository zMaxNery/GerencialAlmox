### Comando para compilar corretamente o projeto
powershell -ExecutionPolicy Bypass -File .\compilador.ps1

### Zerar dados do banco
begin;

truncate table
    public.ajustes_materiais_fabrica,
    public.apontamentos_entrega,
    public.baixas_resumo_totvs,
    public.consumos_materiais_fabrica,
    public.devolucoes_entrega,
    public.emails_importados,
    public.itens_requisicao,
    public.itens_resumo_totvs,
    public.lotes_materiais_fabrica
restart identity;

commit;