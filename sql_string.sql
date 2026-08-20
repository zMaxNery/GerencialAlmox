begin;

-- ============================================================================
-- 0. CONFIGURAÇÃO E LIMPEZA DAS FUNCIONALIDADES MAIS RECENTES
-- ============================================================================
-- A visão de indicadores depende das tabelas operacionais.
drop view if exists public.vw_indicadores_apontamentos cascade;
drop sequence if exists public.seq_requisicao_manual cascade;
drop function if exists public.incluir_requisicao_manual(text,numeric,text,text,text,text,text,numeric,numeric,text) cascade;
drop function if exists public.incluir_material_fabrica_manual(text,text,numeric,text,text) cascade;
drop function if exists public.registrar_entrega_com_fabrica(bigint,numeric,jsonb,text,text) cascade;

-- Controle funcional de acesso por usuário do Windows.
drop function if exists public.app_registrar_ultimo_acesso(bigint) cascade;
drop function if exists public.app_atualizar_atualizado_em() cascade;

drop table if exists
    public.app_usuario_preferencias,
    public.app_usuario_modulos,
    public.app_modulos,
    public.app_usuarios
cascade;


-- Limpeza das rotinas administrativas e das nomenclaturas alternativas.
-- Este bloco torna a recriação segura mesmo quando a base anterior já possuía
-- as telas administrativas ou a versão de nomes organizados.
drop view if exists public.vw_baixas_administrativas_totvs cascade;
drop view if exists public.vw_baixas_resumo_totvs cascade;
drop view if exists public.vw_lancamentos_totvs_pendentes cascade;

drop table if exists public.baixas_resumo_totvs cascade;
drop table if exists public.baixas_administrativas_totvs cascade;

drop function if exists public.marcar_baixa_administrativa_totvs(jsonb, text) cascade;
drop function if exists public.marcar_baixas_resumo_totvs(jsonb, text) cascade;
drop function if exists public.estornar_baixa_resumo_totvs(jsonb, text) cascade;
drop function if exists public.estornar_baixa_administrativa_totvs(jsonb, text) cascade;

drop function if exists public.rpc_totvs_baixar(jsonb, text) cascade;
drop function if exists public.rpc_totvs_estornar(jsonb, text) cascade;
drop function if exists public.rpc_entrega_devolver(bigint, numeric, text, text) cascade;
drop function if exists public.rpc_fabrica_ajustar(bigint, numeric, text, text) cascade;
drop function if exists public.rpc_entrega_mista(bigint, numeric, text, text) cascade;
drop function if exists public.rpc_entrega_fabrica(bigint, numeric, text, text) cascade;
drop function if exists public.rpc_fabrica_consultar(bigint) cascade;
drop function if exists public.rpc_entrega_estoque(bigint, numeric, text, text) cascade;
drop function if exists public.rpc_email_importar(jsonb, jsonb, jsonb) cascade;
drop function if exists public.util_quantidade_entregue(bigint) cascade;
drop function if exists public.util_chave_material(text) cascade;

-- ============================================================================
-- 1. REMOÇÃO DOS OBJETOS ATUAIS E DE VERSÕES ANTERIORES
-- ============================================================================

-- Views atuais.
drop view if exists public.vw_historico_devolucoes cascade;
drop view if exists public.vw_materiais_fabrica cascade;
drop view if exists public.vw_historico_entregas cascade;
drop view if exists public.vw_resumo_totvs cascade;
drop view if exists public.vw_pendencias_est_operador cascade;
drop view if exists public.vw_progresso_requisicoes cascade;

-- Views de versões antigas em inglês.
drop view if exists public.vw_admin_requests cascade;
drop view if exists public.vw_operator_pending_est cascade;
drop view if exists public.vw_request_progress cascade;

-- Funções atuais.
drop function if exists public.devolver_material(bigint, numeric, text, text) cascade;
drop function if exists public.ajustar_material_fabrica(bigint, numeric, text, text) cascade;
drop function if exists public.registrar_entrega_mista(bigint, numeric, text, text) cascade;
drop function if exists public.registrar_entrega_material_fabrica(bigint, numeric, text, text) cascade;
drop function if exists public.consultar_material_fabrica(bigint) cascade;
drop function if exists public.registrar_entrega(bigint, numeric, text, text) cascade;
drop function if exists public.fn_quantidade_entregue_liquida(bigint) cascade;
drop function if exists public.fn_chave_material(text) cascade;
drop function if exists public.importar_email(jsonb, jsonb, jsonb) cascade;

-- Funções de versões antigas em inglês.
drop function if exists public.register_delivery(bigint, numeric, text, text) cascade;
drop function if exists public.import_email(jsonb, jsonb, jsonb) cascade;

-- Tabelas atuais. A lista conjunta permite remover as dependências entre elas.
drop table if exists
    public.ajustes_materiais_fabrica,
    public.consumos_materiais_fabrica,
    public.lotes_materiais_fabrica,
    public.devolucoes_entrega,
    public.apontamentos_entrega,
    public.itens_resumo_totvs,
    public.itens_requisicao,
    public.emails_importados,
    public.importacoes_email
cascade;

-- Tabelas de versões antigas em inglês.
drop table if exists
    public.delivery_entries,
    public.totvs_summary_items,
    public.request_items,
    public.email_imports
cascade;

-- ============================================================================
-- 2. TABELAS PRINCIPAIS
-- ============================================================================

create table public.emails_importados (
    id bigint generated by default as identity primary key,

    hash_arquivo text not null unique,
    nome_arquivo text not null,

    assunto text,
    remetente text,
    recebido_em timestamptz,

    tipo_requisicao text,
    tipo_material text,

    origem_registro text not null default 'EMAIL'
        check (origem_registro in ('EMAIL', 'MANUAL')),

    qtd_material_requisicao integer not null default 0
        check (qtd_material_requisicao >= 0),
    qtd_material_baixa integer not null default 0
        check (qtd_material_baixa >= 0),

    peso_bruto_material numeric(14, 3) not null default 0,
    peso_liquido_material numeric(14, 3) not null default 0,

    importado_por text,
    importado_em timestamptz not null default now()
);

create table public.itens_requisicao (
    id bigint generated by default as identity primary key,

    email_importado_id bigint not null
        references public.emails_importados(id)
        on delete cascade,

    tipo_material text not null,
    tipo_requisicao text not null,

    numero_requisicao text,
    material text,
    dimensao text,
    quantidade numeric(14, 3) not null default 0
        check (quantidade >= 0),

    rastreabilidade text,
    data_requisicao date,
    maquina text,
    localizacao_est text,
    setor_dest text,

    peso_material_kg numeric(14, 3),
    peso_requisitado_kg numeric(14, 3),

    indice_tabela_origem integer,
    indice_linha_origem integer
);

create table public.itens_resumo_totvs (
    id bigint generated by default as identity primary key,

    email_importado_id bigint not null
        references public.emails_importados(id)
        on delete cascade,

    tipo_material text not null,
    tipo_requisicao text not null,

    numero_requisicao text,
    material text,
    os_so text,
    numero_of text,

    peso_material_kg numeric(14, 3),
    peso_requisitado_kg numeric(14, 3),

    indice_tabela_origem integer,
    indice_linha_origem integer
);

create table public.apontamentos_entrega (
    id bigint generated by default as identity primary key,

    item_requisicao_id bigint not null
        references public.itens_requisicao(id)
        on delete cascade,

    -- Quantidade efetivamente aplicada à requisição.
    quantidade_entregue numeric(14, 3) not null
        check (quantidade_entregue > 0),

    -- Quantidade que ultrapassou o restante da requisição e foi para a fábrica.
    quantidade_excedente numeric(14, 3) not null default 0
        check (quantidade_excedente >= 0),

    -- NOVO: saiu do estoque do operador.
    -- FABRICA: foi reaproveitado do saldo existente na fábrica.
    origem_entrega text not null default 'NOVO'
        check (origem_entrega in ('NOVO', 'FABRICA')),

    usuario text not null,
    observacao text,
    entregue_em timestamptz not null default now()
);

create table public.devolucoes_entrega (
    id bigint generated by default as identity primary key,

    apontamento_entrega_id bigint not null
        references public.apontamentos_entrega(id)
        on delete cascade,

    quantidade_devolvida numeric(14, 3) not null
        check (quantidade_devolvida > 0),

    usuario text not null,
    observacao text,
    devolvido_em timestamptz not null default now()
);

-- Cada excedente criado por uma entrega normal gera um lote individual.
create table public.lotes_materiais_fabrica (
    id bigint generated by default as identity primary key,

    apontamento_origem_id bigint unique
        references public.apontamentos_entrega(id)
        on delete set null,

    origem_lote text not null default 'EXCEDENTE'
        check (origem_lote in ('EXCEDENTE', 'MANUAL')),
    observacao_origem text,

    material text not null,
    material_chave text not null,

    rastreabilidade text not null,
    rastreabilidade_chave text not null,

    quantidade_inicial numeric(14, 3) not null
        check (quantidade_inicial > 0),

    -- Pode ser maior que a inicial após ajuste manual; nunca pode ser negativa.
    quantidade_disponivel numeric(14, 3) not null
        check (quantidade_disponivel >= 0),

    usuario text not null,
    recebido_em timestamptz not null default now()
);

-- Relaciona uma entrega de origem FABRICA aos lotes efetivamente consumidos.
create table public.consumos_materiais_fabrica (
    id bigint generated by default as identity primary key,

    lote_material_fabrica_id bigint not null
        references public.lotes_materiais_fabrica(id),

    apontamento_destino_id bigint not null
        references public.apontamentos_entrega(id)
        on delete cascade,

    quantidade_consumida numeric(14, 3) not null
        check (quantidade_consumida > 0),

    quantidade_estornada numeric(14, 3) not null default 0
        check (
            quantidade_estornada >= 0
            and quantidade_estornada <= quantidade_consumida
        ),

    usuario text not null,
    consumido_em timestamptz not null default now()
);

-- Auditoria de alterações manuais e zeramentos automáticos dos lotes.
create table public.ajustes_materiais_fabrica (
    id bigint generated by default as identity primary key,

    lote_material_fabrica_id bigint not null
        references public.lotes_materiais_fabrica(id)
        on delete cascade,

    quantidade_anterior numeric(14, 3) not null,
    quantidade_nova numeric(14, 3) not null
        check (quantidade_nova >= 0),
    diferenca numeric(14, 3) not null,

    usuario text not null,
    observacao text,
    motivo text not null default 'AJUSTE_MANUAL',
    ajustado_em timestamptz not null default now()
);

-- ============================================================================
-- 3. ÍNDICES
-- ============================================================================

create index idx_itens_requisicao_importacao
    on public.itens_requisicao(email_importado_id);

create index idx_itens_requisicao_material_rastreabilidade
    on public.itens_requisicao(material, rastreabilidade);

create index idx_itens_requisicao_data
    on public.itens_requisicao(data_requisicao);

create index idx_itens_requisicao_numero
    on public.itens_requisicao(numero_requisicao)
    where numero_requisicao is not null;

create sequence public.seq_requisicao_manual start with 1 increment by 1;

create index idx_itens_resumo_importacao
    on public.itens_resumo_totvs(email_importado_id);

create index idx_itens_resumo_requisicao
    on public.itens_resumo_totvs(numero_requisicao);

create index idx_apontamentos_item
    on public.apontamentos_entrega(item_requisicao_id);

create index idx_apontamentos_data
    on public.apontamentos_entrega(entregue_em);

create index idx_devolucoes_apontamento
    on public.devolucoes_entrega(apontamento_entrega_id);

create index idx_devolucoes_data
    on public.devolucoes_entrega(devolvido_em);

create index idx_lotes_fabrica_chaves
    on public.lotes_materiais_fabrica(
        material_chave,
        rastreabilidade_chave,
        recebido_em,
        id
    );

create index idx_lotes_fabrica_disponivel
    on public.lotes_materiais_fabrica(quantidade_disponivel)
    where quantidade_disponivel > 0;

create index idx_consumos_fabrica_destino
    on public.consumos_materiais_fabrica(apontamento_destino_id);

create index idx_consumos_fabrica_lote
    on public.consumos_materiais_fabrica(lote_material_fabrica_id);

create index idx_ajustes_fabrica_lote
    on public.ajustes_materiais_fabrica(lote_material_fabrica_id);

-- ============================================================================
-- 4. FUNÇÕES AUXILIARES
-- ============================================================================

-- Normaliza a combinação Material x Rastreabilidade.
create function public.fn_chave_material(p_valor text)
returns text
language sql
immutable
set search_path = public
as $$
    select upper(
        regexp_replace(
            btrim(coalesce(p_valor, '')),
            '[[:space:]]+',
            ' ',
            'g'
        )
    );
$$;

-- Soma somente a parcela líquida ainda válida dos apontamentos da requisição.
create function public.fn_quantidade_entregue_liquida(
    p_item_requisicao_id bigint
)
returns numeric
language sql
stable
set search_path = public
as $$
    select coalesce(
        sum(
            greatest(
                ae.quantidade_entregue
                - coalesce(devolucao.quantidade_devolvida, 0),
                0
            )
        ),
        0
    )::numeric(14, 3)
    from public.apontamentos_entrega ae
    left join lateral (
        select coalesce(sum(de.quantidade_devolvida), 0)
            as quantidade_devolvida
        from public.devolucoes_entrega de
        where de.apontamento_entrega_id = ae.id
    ) devolucao on true
    where ae.item_requisicao_id = p_item_requisicao_id;
$$;

-- ============================================================================
-- 5. RPC: IMPORTAÇÃO DO E-MAIL
--    Aceita tanto o payload atual em inglês quanto as chaves em português.
-- ============================================================================

create function public.importar_email(
    p_email jsonb,
    p_itens_requisicao jsonb,
    p_itens_resumo jsonb
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_importacao_id bigint;
    v_id_existente bigint;

    v_hash_arquivo text;
    v_nome_arquivo text;
    v_assunto text;
    v_remetente text;
    v_recebido_em text;
    v_tipo_requisicao text;
    v_tipo_material text;
    v_importado_por text;

    v_item jsonb;

    v_qtd_material_requisicao integer;
    v_qtd_material_baixa integer;
    v_peso_bruto_material numeric(14, 3);
    v_peso_liquido_material numeric(14, 3);
begin
    v_hash_arquivo := coalesce(
        nullif(p_email->>'hash_arquivo', ''),
        nullif(p_email->>'file_hash', '')
    );

    v_nome_arquivo := coalesce(
        nullif(p_email->>'nome_arquivo', ''),
        nullif(p_email->>'file_name', '')
    );

    v_assunto := coalesce(
        p_email->>'assunto',
        p_email->>'subject'
    );

    v_remetente := coalesce(
        p_email->>'remetente',
        p_email->>'sender'
    );

    v_recebido_em := coalesce(
        nullif(p_email->>'recebido_em', ''),
        nullif(p_email->>'received_at', '')
    );

    v_tipo_requisicao := upper(coalesce(
        nullif(p_email->>'tipo_requisicao', ''),
        nullif(p_email->>'stock_location', ''),
        ''
    ));

    v_tipo_material := coalesce(
        p_email->>'tipo_material',
        p_email->>'movement_type'
    );

    v_importado_por := coalesce(
        p_email->>'importado_por',
        p_email->>'imported_by'
    );

    if v_hash_arquivo is null then
        raise exception 'O payload do e-mail não contém o hash do arquivo.';
    end if;

    if v_nome_arquivo is null then
        raise exception 'O payload do e-mail não contém o nome do arquivo.';
    end if;

    insert into public.emails_importados (
        hash_arquivo,
        nome_arquivo,
        assunto,
        remetente,
        recebido_em,
        tipo_requisicao,
        tipo_material,
        importado_por
    )
    values (
        v_hash_arquivo,
        v_nome_arquivo,
        v_assunto,
        v_remetente,
        v_recebido_em::timestamptz,
        nullif(v_tipo_requisicao, ''),
        v_tipo_material,
        v_importado_por
    )
    on conflict (hash_arquivo) do nothing
    returning id into v_importacao_id;

    if v_importacao_id is null then
        select id
        into v_id_existente
        from public.emails_importados
        where hash_arquivo = v_hash_arquivo;

        return jsonb_build_object(
            'status', 'DUPLICADO',
            'importacao_id', v_id_existente
        );
    end if;

    for v_item in
        select value
        from jsonb_array_elements(
            coalesce(p_itens_requisicao, '[]'::jsonb)
        )
    loop
        insert into public.itens_requisicao (
            email_importado_id,
            tipo_material,
            tipo_requisicao,
            material,
            dimensao,
            quantidade,
            rastreabilidade,
            data_requisicao,
            maquina,
            localizacao_est,
            setor_dest,
            peso_material_kg,
            peso_requisitado_kg,
            indice_tabela_origem,
            indice_linha_origem
        )
        values (
            v_importacao_id,
            coalesce(
                nullif(v_item->>'tipo_material', ''),
                nullif(v_item->>'material_type', ''),
                'NAO_INFORMADO'
            ),
            upper(coalesce(
                nullif(v_item->>'tipo_requisicao', ''),
                nullif(v_item->>'stock_location', ''),
                nullif(v_tipo_requisicao, ''),
                'NAO_INFORMADO'
            )),
            coalesce(v_item->>'material', ''),
            coalesce(v_item->>'dimensao', v_item->>'dimension', ''),
            coalesce(
                nullif(v_item->>'quantidade', '')::numeric,
                nullif(v_item->>'quantity', '')::numeric,
                0
            ),
            coalesce(v_item->>'rastreabilidade', v_item->>'traceability', ''),
            nullif(coalesce(
                v_item->>'data_requisicao',
                v_item->>'request_date',
                ''
            ), '')::date,
            coalesce(v_item->>'maquina', v_item->>'machine', ''),
            coalesce(v_item->>'localizacao_est', v_item->>'location', ''),
            coalesce(v_item->>'setor_dest', v_item->>'sector', ''),
            coalesce(
                nullif(v_item->>'peso_material_kg', '')::numeric,
                nullif(v_item->>'material_weight_kg', '')::numeric
            ),
            coalesce(
                nullif(v_item->>'peso_requisitado_kg', '')::numeric,
                nullif(v_item->>'requested_weight_kg', '')::numeric
            ),
            coalesce(
                nullif(v_item->>'indice_tabela_origem', '')::integer,
                nullif(v_item->>'source_table_index', '')::integer
            ),
            coalesce(
                nullif(v_item->>'indice_linha_origem', '')::integer,
                nullif(v_item->>'source_row_index', '')::integer
            )
        );
    end loop;

    for v_item in
        select value
        from jsonb_array_elements(
            coalesce(p_itens_resumo, '[]'::jsonb)
        )
    loop
        insert into public.itens_resumo_totvs (
            email_importado_id,
            tipo_material,
            tipo_requisicao,
            numero_requisicao,
            material,
            os_so,
            numero_of,
            peso_material_kg,
            peso_requisitado_kg,
            indice_tabela_origem,
            indice_linha_origem
        )
        values (
            v_importacao_id,
            coalesce(
                nullif(v_item->>'tipo_material', ''),
                nullif(v_item->>'material_type', ''),
                'NAO_INFORMADO'
            ),
            upper(coalesce(
                nullif(v_item->>'tipo_requisicao', ''),
                nullif(v_item->>'stock_location', ''),
                nullif(v_tipo_requisicao, ''),
                'NAO_INFORMADO'
            )),
            coalesce(v_item->>'numero_requisicao', v_item->>'request_number', ''),
            coalesce(v_item->>'material', ''),
            coalesce(v_item->>'os_so', ''),
            coalesce(v_item->>'numero_of', v_item->>'of_number', ''),
            coalesce(
                nullif(v_item->>'peso_material_kg', '')::numeric,
                nullif(v_item->>'material_weight_kg', '')::numeric
            ),
            coalesce(
                nullif(v_item->>'peso_requisitado_kg', '')::numeric,
                nullif(v_item->>'requested_weight_kg', '')::numeric
            ),
            coalesce(
                nullif(v_item->>'indice_tabela_origem', '')::integer,
                nullif(v_item->>'source_table_index', '')::integer
            ),
            coalesce(
                nullif(v_item->>'indice_linha_origem', '')::integer,
                nullif(v_item->>'source_row_index', '')::integer
            )
        );
    end loop;

    select
        count(*),
        coalesce(sum(peso_material_kg), 0)
    into
        v_qtd_material_requisicao,
        v_peso_bruto_material
    from public.itens_requisicao
    where email_importado_id = v_importacao_id;

    select
        count(*),
        coalesce(sum(peso_requisitado_kg), 0)
    into
        v_qtd_material_baixa,
        v_peso_liquido_material
    from public.itens_resumo_totvs
    where email_importado_id = v_importacao_id;

    update public.emails_importados
    set
        qtd_material_requisicao = v_qtd_material_requisicao,
        qtd_material_baixa = v_qtd_material_baixa,
        peso_bruto_material = v_peso_bruto_material,
        peso_liquido_material = v_peso_liquido_material
    where id = v_importacao_id;

    return jsonb_build_object(
        'status', 'IMPORTADO',
        'importacao_id', v_importacao_id,
        'qtd_material_requisicao', v_qtd_material_requisicao,
        'qtd_material_baixa', v_qtd_material_baixa,
        'peso_bruto_material', v_peso_bruto_material,
        'peso_liquido_material', v_peso_liquido_material
    );
end;
$$;

-- ============================================================================
-- 6. RPC: ENTREGA NORMAL / MATERIAL NOVO
-- ============================================================================

create function public.registrar_entrega(
    p_item_requisicao_id bigint,
    p_quantidade numeric,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_quantidade_solicitada numeric(14, 3);
    v_quantidade_ja_entregue numeric(14, 3);
    v_quantidade_restante numeric(14, 3);
    v_quantidade_aplicada numeric(14, 3);
    v_quantidade_excedente numeric(14, 3);
    v_material text;
    v_rastreabilidade text;
    v_tipo_requisicao text;
    v_apontamento_id bigint;
begin
    if p_quantidade is null or p_quantidade <= 0 then
        raise exception 'A quantidade entregue deve ser maior que zero.';
    end if;

    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    select
        ir.quantidade,
        ir.material,
        ir.rastreabilidade,
        ir.tipo_requisicao
    into
        v_quantidade_solicitada,
        v_material,
        v_rastreabilidade,
        v_tipo_requisicao
    from public.itens_requisicao ir
    where ir.id = p_item_requisicao_id
    for update;

    if not found then
        raise exception 'Item de requisição não encontrado.';
    end if;

    if upper(coalesce(v_tipo_requisicao, '')) <> 'EST' then
        raise exception 'Somente itens EST recebem apontamento de entrega.';
    end if;

    v_quantidade_ja_entregue :=
        public.fn_quantidade_entregue_liquida(p_item_requisicao_id);

    v_quantidade_restante := greatest(
        v_quantidade_solicitada - v_quantidade_ja_entregue,
        0
    );

    if v_quantidade_restante <= 0 then
        raise exception 'A requisição já está totalmente atendida.';
    end if;

    v_quantidade_aplicada := least(p_quantidade, v_quantidade_restante);
    v_quantidade_excedente := greatest(
        p_quantidade - v_quantidade_aplicada,
        0
    );

    if v_quantidade_excedente > 0
       and (
            nullif(btrim(v_material), '') is null
            or nullif(btrim(v_rastreabilidade), '') is null
       ) then
        raise exception
            'Não é possível registrar excedente sem material e rastreabilidade.';
    end if;

    insert into public.apontamentos_entrega (
        item_requisicao_id,
        quantidade_entregue,
        quantidade_excedente,
        origem_entrega,
        usuario,
        observacao
    )
    values (
        p_item_requisicao_id,
        v_quantidade_aplicada,
        v_quantidade_excedente,
        'NOVO',
        btrim(p_usuario),
        nullif(btrim(p_observacao), '')
    )
    returning id into v_apontamento_id;

    if v_quantidade_excedente > 0 then
        insert into public.lotes_materiais_fabrica (
            apontamento_origem_id,
            material,
            material_chave,
            rastreabilidade,
            rastreabilidade_chave,
            quantidade_inicial,
            quantidade_disponivel,
            usuario
        )
        values (
            v_apontamento_id,
            btrim(v_material),
            public.fn_chave_material(v_material),
            btrim(v_rastreabilidade),
            public.fn_chave_material(v_rastreabilidade),
            v_quantidade_excedente,
            v_quantidade_excedente,
            btrim(p_usuario)
        );
    end if;

    return jsonb_build_object(
        'status', 'REGISTRADO',
        'apontamento_entrega_id', v_apontamento_id,
        'quantidade_informada', p_quantidade,
        'quantidade_aplicada', v_quantidade_aplicada,
        'quantidade_excedente', v_quantidade_excedente,
        'quantidade_restante', greatest(
            v_quantidade_restante - v_quantidade_aplicada,
            0
        )
    );
end;
$$;

-- ============================================================================
-- 7. RPC: CONSULTAR MATERIAL EM FÁBRICA
-- ============================================================================

create function public.consultar_material_fabrica(
    p_item_requisicao_id bigint
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_material text;
    v_rastreabilidade text;
    v_quantidade_solicitada numeric(14, 3);
    v_quantidade_entregue numeric(14, 3);
    v_quantidade_disponivel numeric(14, 3);
begin
    select
        ir.material,
        ir.rastreabilidade,
        ir.quantidade
    into
        v_material,
        v_rastreabilidade,
        v_quantidade_solicitada
    from public.itens_requisicao ir
    where ir.id = p_item_requisicao_id;

    if not found then
        raise exception 'Item de requisição não encontrado.';
    end if;

    v_quantidade_entregue :=
        public.fn_quantidade_entregue_liquida(p_item_requisicao_id);

    select coalesce(sum(lmf.quantidade_disponivel), 0)
    into v_quantidade_disponivel
    from public.lotes_materiais_fabrica lmf
    where lmf.material_chave = public.fn_chave_material(v_material)
      and lmf.rastreabilidade_chave = public.fn_chave_material(v_rastreabilidade)
      and lmf.quantidade_disponivel > 0;

    return jsonb_build_object(
        'item_requisicao_id', p_item_requisicao_id,
        'material', v_material,
        'rastreabilidade', v_rastreabilidade,
        'quantidade_restante_requisicao', greatest(
            v_quantidade_solicitada - v_quantidade_entregue,
            0
        ),
        'quantidade_disponivel', v_quantidade_disponivel
    );
end;
$$;

-- ============================================================================
-- 8. RPC: ENTREGA PARCIAL USANDO SOMENTE MATERIAL DA FÁBRICA
-- ============================================================================

create function public.registrar_entrega_material_fabrica(
    p_item_requisicao_id bigint,
    p_quantidade_fabrica numeric,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_quantidade_solicitada numeric(14, 3);
    v_quantidade_entregue numeric(14, 3);
    v_quantidade_restante numeric(14, 3);
    v_quantidade_disponivel numeric(14, 3);
    v_material text;
    v_rastreabilidade text;
    v_tipo_requisicao text;
    v_apontamento_id bigint;
    v_faltante numeric(14, 3);
    v_consumir numeric(14, 3);
    v_lote record;
begin
    if p_quantidade_fabrica is null or p_quantidade_fabrica <= 0 then
        raise exception 'A quantidade da fábrica deve ser maior que zero.';
    end if;

    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    select
        ir.quantidade,
        ir.material,
        ir.rastreabilidade,
        ir.tipo_requisicao
    into
        v_quantidade_solicitada,
        v_material,
        v_rastreabilidade,
        v_tipo_requisicao
    from public.itens_requisicao ir
    where ir.id = p_item_requisicao_id
    for update;

    if not found then
        raise exception 'Item de requisição não encontrado.';
    end if;

    if upper(coalesce(v_tipo_requisicao, '')) <> 'EST' then
        raise exception 'Somente itens EST recebem apontamento de entrega.';
    end if;

    if nullif(btrim(v_material), '') is null
       or nullif(btrim(v_rastreabilidade), '') is null then
        raise exception 'A requisição precisa ter material e rastreabilidade.';
    end if;

    v_quantidade_entregue :=
        public.fn_quantidade_entregue_liquida(p_item_requisicao_id);

    v_quantidade_restante := greatest(
        v_quantidade_solicitada - v_quantidade_entregue,
        0
    );

    if v_quantidade_restante <= 0 then
        raise exception 'A requisição já está totalmente atendida.';
    end if;

    if p_quantidade_fabrica > v_quantidade_restante then
        raise exception
            'A quantidade da fábrica (%) é maior que o restante da requisição (%).',
            p_quantidade_fabrica,
            v_quantidade_restante;
    end if;

    -- Bloqueia todos os lotes candidatos antes de validar o saldo.
    select coalesce(sum(lote.quantidade_disponivel), 0)
    into v_quantidade_disponivel
    from (
        select
            lmf.id,
            lmf.quantidade_disponivel
        from public.lotes_materiais_fabrica lmf
        where lmf.material_chave = public.fn_chave_material(v_material)
          and lmf.rastreabilidade_chave = public.fn_chave_material(v_rastreabilidade)
          and lmf.quantidade_disponivel > 0
        order by lmf.recebido_em, lmf.id
        for update
    ) lote;

    if p_quantidade_fabrica > v_quantidade_disponivel then
        raise exception
            'Saldo em fábrica insuficiente. Disponível: %.',
            v_quantidade_disponivel;
    end if;

    insert into public.apontamentos_entrega (
        item_requisicao_id,
        quantidade_entregue,
        quantidade_excedente,
        origem_entrega,
        usuario,
        observacao
    )
    values (
        p_item_requisicao_id,
        p_quantidade_fabrica,
        0,
        'FABRICA',
        btrim(p_usuario),
        nullif(btrim(p_observacao), '')
    )
    returning id into v_apontamento_id;

    v_faltante := p_quantidade_fabrica;

    for v_lote in
        select
            lmf.id,
            lmf.quantidade_disponivel
        from public.lotes_materiais_fabrica lmf
        where lmf.material_chave = public.fn_chave_material(v_material)
          and lmf.rastreabilidade_chave = public.fn_chave_material(v_rastreabilidade)
          and lmf.quantidade_disponivel > 0
        order by lmf.recebido_em, lmf.id
        for update
    loop
        exit when v_faltante <= 0;

        v_consumir := least(v_lote.quantidade_disponivel, v_faltante);

        update public.lotes_materiais_fabrica
        set quantidade_disponivel = quantidade_disponivel - v_consumir
        where id = v_lote.id;

        insert into public.consumos_materiais_fabrica (
            lote_material_fabrica_id,
            apontamento_destino_id,
            quantidade_consumida,
            quantidade_estornada,
            usuario
        )
        values (
            v_lote.id,
            v_apontamento_id,
            v_consumir,
            0,
            btrim(p_usuario)
        );

        v_faltante := v_faltante - v_consumir;
    end loop;

    if v_faltante > 0 then
        raise exception
            'O saldo em fábrica foi alterado por outro usuário. Tente novamente.';
    end if;

    return jsonb_build_object(
        'status', 'REGISTRADO_FABRICA',
        'apontamento_entrega_id', v_apontamento_id,
        'quantidade_fabrica', p_quantidade_fabrica,
        'quantidade_nova_aplicada', 0,
        'quantidade_excedente', 0,
        'quantidade_restante', greatest(
            v_quantidade_restante - p_quantidade_fabrica,
            0
        )
    );
end;
$$;

-- ============================================================================
-- 9. RPC: ENTREGA MISTA
--    Usa todo o saldo possível da fábrica e depois o material novo informado.
-- ============================================================================

create function public.registrar_entrega_mista(
    p_item_requisicao_id bigint,
    p_quantidade_nova numeric,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_quantidade_solicitada numeric(14, 3);
    v_quantidade_entregue numeric(14, 3);
    v_quantidade_restante numeric(14, 3);
    v_quantidade_disponivel numeric(14, 3);
    v_quantidade_fabrica numeric(14, 3);
    v_restante_apos_fabrica numeric(14, 3);
    v_quantidade_nova_aplicada numeric(14, 3);
    v_quantidade_excedente numeric(14, 3);
    v_material text;
    v_rastreabilidade text;
    v_tipo_requisicao text;
    v_apontamento_fabrica_id bigint;
    v_apontamento_novo_id bigint;
    v_faltante numeric(14, 3);
    v_consumir numeric(14, 3);
    v_lote record;
begin
    if p_quantidade_nova is null or p_quantidade_nova <= 0 then
        raise exception 'A quantidade de material novo deve ser maior que zero.';
    end if;

    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    select
        ir.quantidade,
        ir.material,
        ir.rastreabilidade,
        ir.tipo_requisicao
    into
        v_quantidade_solicitada,
        v_material,
        v_rastreabilidade,
        v_tipo_requisicao
    from public.itens_requisicao ir
    where ir.id = p_item_requisicao_id
    for update;

    if not found then
        raise exception 'Item de requisição não encontrado.';
    end if;

    if upper(coalesce(v_tipo_requisicao, '')) <> 'EST' then
        raise exception 'Somente itens EST recebem apontamento de entrega.';
    end if;

    if nullif(btrim(v_material), '') is null
       or nullif(btrim(v_rastreabilidade), '') is null then
        raise exception 'A requisição precisa ter material e rastreabilidade.';
    end if;

    v_quantidade_entregue :=
        public.fn_quantidade_entregue_liquida(p_item_requisicao_id);

    v_quantidade_restante := greatest(
        v_quantidade_solicitada - v_quantidade_entregue,
        0
    );

    if v_quantidade_restante <= 0 then
        raise exception 'A requisição já está totalmente atendida.';
    end if;

    -- Bloqueia todos os lotes candidatos antes de calcular o saldo.
    select coalesce(sum(lote.quantidade_disponivel), 0)
    into v_quantidade_disponivel
    from (
        select
            lmf.id,
            lmf.quantidade_disponivel
        from public.lotes_materiais_fabrica lmf
        where lmf.material_chave = public.fn_chave_material(v_material)
          and lmf.rastreabilidade_chave = public.fn_chave_material(v_rastreabilidade)
          and lmf.quantidade_disponivel > 0
        order by lmf.recebido_em, lmf.id
        for update
    ) lote;

    v_quantidade_fabrica := least(
        v_quantidade_disponivel,
        v_quantidade_restante
    );

    if v_quantidade_fabrica <= 0 then
        raise exception 'Não há saldo deste material e rastreabilidade na fábrica.';
    end if;

    v_restante_apos_fabrica :=
        v_quantidade_restante - v_quantidade_fabrica;

    if v_restante_apos_fabrica <= 0 then
        raise exception
            'O saldo em fábrica já atende toda a requisição. Use a opção Somente fábrica.';
    end if;

    v_quantidade_nova_aplicada := least(
        p_quantidade_nova,
        v_restante_apos_fabrica
    );

    v_quantidade_excedente := greatest(
        p_quantidade_nova - v_quantidade_nova_aplicada,
        0
    );

    -- Primeiro apontamento: parcela reaproveitada da fábrica.
    insert into public.apontamentos_entrega (
        item_requisicao_id,
        quantidade_entregue,
        quantidade_excedente,
        origem_entrega,
        usuario,
        observacao
    )
    values (
        p_item_requisicao_id,
        v_quantidade_fabrica,
        0,
        'FABRICA',
        btrim(p_usuario),
        nullif(btrim(p_observacao), '')
    )
    returning id into v_apontamento_fabrica_id;

    v_faltante := v_quantidade_fabrica;

    for v_lote in
        select
            lmf.id,
            lmf.quantidade_disponivel
        from public.lotes_materiais_fabrica lmf
        where lmf.material_chave = public.fn_chave_material(v_material)
          and lmf.rastreabilidade_chave = public.fn_chave_material(v_rastreabilidade)
          and lmf.quantidade_disponivel > 0
        order by lmf.recebido_em, lmf.id
        for update
    loop
        exit when v_faltante <= 0;

        v_consumir := least(v_lote.quantidade_disponivel, v_faltante);

        update public.lotes_materiais_fabrica
        set quantidade_disponivel = quantidade_disponivel - v_consumir
        where id = v_lote.id;

        insert into public.consumos_materiais_fabrica (
            lote_material_fabrica_id,
            apontamento_destino_id,
            quantidade_consumida,
            quantidade_estornada,
            usuario
        )
        values (
            v_lote.id,
            v_apontamento_fabrica_id,
            v_consumir,
            0,
            btrim(p_usuario)
        );

        v_faltante := v_faltante - v_consumir;
    end loop;

    if v_faltante > 0 then
        raise exception
            'O saldo em fábrica foi alterado por outro usuário. Tente novamente.';
    end if;

    -- Segundo apontamento: material novo enviado pelo estoque.
    insert into public.apontamentos_entrega (
        item_requisicao_id,
        quantidade_entregue,
        quantidade_excedente,
        origem_entrega,
        usuario,
        observacao
    )
    values (
        p_item_requisicao_id,
        v_quantidade_nova_aplicada,
        v_quantidade_excedente,
        'NOVO',
        btrim(p_usuario),
        nullif(btrim(p_observacao), '')
    )
    returning id into v_apontamento_novo_id;

    if v_quantidade_excedente > 0 then
        insert into public.lotes_materiais_fabrica (
            apontamento_origem_id,
            material,
            material_chave,
            rastreabilidade,
            rastreabilidade_chave,
            quantidade_inicial,
            quantidade_disponivel,
            usuario
        )
        values (
            v_apontamento_novo_id,
            btrim(v_material),
            public.fn_chave_material(v_material),
            btrim(v_rastreabilidade),
            public.fn_chave_material(v_rastreabilidade),
            v_quantidade_excedente,
            v_quantidade_excedente,
            btrim(p_usuario)
        );
    end if;

    return jsonb_build_object(
        'status', 'REGISTRADO_MISTO',
        'apontamento_fabrica_id', v_apontamento_fabrica_id,
        'apontamento_novo_id', v_apontamento_novo_id,
        'quantidade_fabrica', v_quantidade_fabrica,
        'quantidade_nova_aplicada', v_quantidade_nova_aplicada,
        'quantidade_excedente', v_quantidade_excedente,
        'quantidade_restante', greatest(
            v_quantidade_restante
            - v_quantidade_fabrica
            - v_quantidade_nova_aplicada,
            0
        )
    );
end;
$$;

-- ============================================================================
-- 10. RPC: AJUSTAR MANUALMENTE O SALDO DE UM LOTE
-- ============================================================================

create function public.ajustar_material_fabrica(
    p_lote_material_fabrica_id bigint,
    p_nova_quantidade numeric,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_quantidade_anterior numeric(14, 3);
begin
    if p_nova_quantidade is null or p_nova_quantidade < 0 then
        raise exception 'A nova quantidade não pode ser negativa.';
    end if;

    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    select quantidade_disponivel
    into v_quantidade_anterior
    from public.lotes_materiais_fabrica
    where id = p_lote_material_fabrica_id
    for update;

    if not found then
        raise exception 'Lote de material em fábrica não encontrado.';
    end if;

    update public.lotes_materiais_fabrica
    set quantidade_disponivel = p_nova_quantidade
    where id = p_lote_material_fabrica_id;

    insert into public.ajustes_materiais_fabrica (
        lote_material_fabrica_id,
        quantidade_anterior,
        quantidade_nova,
        diferenca,
        usuario,
        observacao,
        motivo
    )
    values (
        p_lote_material_fabrica_id,
        v_quantidade_anterior,
        p_nova_quantidade,
        p_nova_quantidade - v_quantidade_anterior,
        btrim(p_usuario),
        nullif(btrim(p_observacao), ''),
        'AJUSTE_MANUAL'
    );

    return jsonb_build_object(
        'status', 'AJUSTADO',
        'lote_material_fabrica_id', p_lote_material_fabrica_id,
        'quantidade_anterior', v_quantidade_anterior,
        'quantidade_nova', p_nova_quantidade,
        'oculto_da_tela', p_nova_quantidade = 0
    );
end;
$$;

-- ============================================================================
-- 11. RPC: DEVOLUÇÃO
--     FABRICA: devolve a quantidade aos lotes consumidos.
--     NOVO: se a entrega for totalmente devolvida, zera o excedente disponível.
-- ============================================================================

create function public.devolver_material(
    p_apontamento_entrega_id bigint,
    p_quantidade numeric,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_quantidade_original numeric(14, 3);
    v_quantidade_excedente numeric(14, 3);
    v_quantidade_ja_devolvida numeric(14, 3);
    v_quantidade_disponivel_devolucao numeric(14, 3);
    v_quantidade_restante_apontamento numeric(14, 3);
    v_origem_entrega text;
    v_devolucao_id bigint;

    v_a_estornar numeric(14, 3);
    v_estornar numeric(14, 3);
    v_consumo record;
    v_lote record;
begin
    if p_quantidade is null or p_quantidade <= 0 then
        raise exception 'A quantidade devolvida deve ser maior que zero.';
    end if;

    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    select
        ae.quantidade_entregue,
        ae.quantidade_excedente,
        ae.origem_entrega
    into
        v_quantidade_original,
        v_quantidade_excedente,
        v_origem_entrega
    from public.apontamentos_entrega ae
    where ae.id = p_apontamento_entrega_id
    for update;

    if not found then
        raise exception 'Apontamento de entrega não encontrado.';
    end if;

    select coalesce(sum(de.quantidade_devolvida), 0)
    into v_quantidade_ja_devolvida
    from public.devolucoes_entrega de
    where de.apontamento_entrega_id = p_apontamento_entrega_id;

    v_quantidade_disponivel_devolucao :=
        v_quantidade_original - v_quantidade_ja_devolvida;

    if p_quantidade > v_quantidade_disponivel_devolucao then
        raise exception
            'A quantidade informada (%) é maior que a disponível para devolução (%).',
            p_quantidade,
            v_quantidade_disponivel_devolucao;
    end if;

    insert into public.devolucoes_entrega (
        apontamento_entrega_id,
        quantidade_devolvida,
        usuario,
        observacao
    )
    values (
        p_apontamento_entrega_id,
        p_quantidade,
        btrim(p_usuario),
        nullif(btrim(p_observacao), '')
    )
    returning id into v_devolucao_id;

    v_quantidade_restante_apontamento :=
        v_quantidade_disponivel_devolucao - p_quantidade;

    -- Uma devolução de material reaproveitado retorna aos mesmos lotes.
    if v_origem_entrega = 'FABRICA' then
        v_a_estornar := p_quantidade;

        for v_consumo in
            select
                cmf.id,
                cmf.lote_material_fabrica_id,
                cmf.quantidade_consumida - cmf.quantidade_estornada
                    as quantidade_restauravel
            from public.consumos_materiais_fabrica cmf
            where cmf.apontamento_destino_id = p_apontamento_entrega_id
              and cmf.quantidade_consumida - cmf.quantidade_estornada > 0
            order by cmf.id desc
            for update
        loop
            exit when v_a_estornar <= 0;

            v_estornar := least(
                v_consumo.quantidade_restauravel,
                v_a_estornar
            );

            update public.consumos_materiais_fabrica
            set quantidade_estornada = quantidade_estornada + v_estornar
            where id = v_consumo.id;

            -- Bloqueia o lote antes de devolver o saldo.
            perform 1
            from public.lotes_materiais_fabrica
            where id = v_consumo.lote_material_fabrica_id
            for update;

            update public.lotes_materiais_fabrica
            set quantidade_disponivel = quantidade_disponivel + v_estornar
            where id = v_consumo.lote_material_fabrica_id;

            v_a_estornar := v_a_estornar - v_estornar;
        end loop;

        if v_a_estornar > 0 then
            raise exception
                'Inconsistência no consumo dos lotes. Não foi possível estornar %.',
                v_a_estornar;
        end if;
    end if;

    -- Se a entrega NOVA foi totalmente devolvida, remove da fábrica todo o
    -- excedente dessa entrega que ainda não tinha sido consumido.
    if v_origem_entrega = 'NOVO'
       and v_quantidade_restante_apontamento <= 0
       and v_quantidade_excedente > 0 then
        for v_lote in
            select
                lmf.id,
                lmf.quantidade_disponivel
            from public.lotes_materiais_fabrica lmf
            where lmf.apontamento_origem_id = p_apontamento_entrega_id
              and lmf.quantidade_disponivel > 0
            for update
        loop
            insert into public.ajustes_materiais_fabrica (
                lote_material_fabrica_id,
                quantidade_anterior,
                quantidade_nova,
                diferenca,
                usuario,
                observacao,
                motivo
            )
            values (
                v_lote.id,
                v_lote.quantidade_disponivel,
                0,
                -v_lote.quantidade_disponivel,
                btrim(p_usuario),
                coalesce(
                    nullif(btrim(p_observacao), ''),
                    'Excedente removido após devolução total da entrega.'
                ),
                'DEVOLUCAO_TOTAL_DA_ENTREGA'
            );

            update public.lotes_materiais_fabrica
            set quantidade_disponivel = 0
            where id = v_lote.id;
        end loop;
    end if;

    return jsonb_build_object(
        'status', 'DEVOLVIDO',
        'devolucao_id', v_devolucao_id,
        'apontamento_entrega_id', p_apontamento_entrega_id,
        'quantidade_devolvida', p_quantidade,
        'quantidade_entregue_restante', v_quantidade_restante_apontamento,
        'origem_entrega', v_origem_entrega
    );
end;
$$;

-- ============================================================================
-- 11-A. RPC: CONSULTA DE FÁBRICA POR MATERIAL (QUALQUER RASTREABILIDADE)
-- ============================================================================

create or replace function public.consultar_material_fabrica(
    p_item_requisicao_id bigint
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_material text;
    v_rastreabilidade text;
    v_quantidade_solicitada numeric(14, 3);
    v_quantidade_entregue numeric(14, 3);
    v_quantidade_disponivel numeric(14, 3);
    v_lotes jsonb;
begin
    select
        ir.material,
        ir.rastreabilidade,
        ir.quantidade
    into
        v_material,
        v_rastreabilidade,
        v_quantidade_solicitada
    from public.itens_requisicao ir
    where ir.id = p_item_requisicao_id;

    if not found then
        raise exception 'Item de requisição não encontrado.';
    end if;

    v_quantidade_entregue :=
        public.fn_quantidade_entregue_liquida(p_item_requisicao_id);

    select coalesce(sum(lmf.quantidade_disponivel), 0)
    into v_quantidade_disponivel
    from public.lotes_materiais_fabrica lmf
    where lmf.material_chave = public.fn_chave_material(v_material)
      and lmf.quantidade_disponivel > 0;

    select coalesce(
        jsonb_agg(
            jsonb_build_object(
                'lote_id', lote.id,
                'rastreabilidade', lote.rastreabilidade,
                'quantidade_disponivel', lote.quantidade_disponivel,
                'recebido_em', lote.recebido_em,
                'origem_lote', lote.origem_lote
            )
            order by lote.recebido_em, lote.id
        ),
        '[]'::jsonb
    )
    into v_lotes
    from (
        select
            lmf.id,
            lmf.rastreabilidade,
            lmf.quantidade_disponivel,
            lmf.recebido_em,
            lmf.origem_lote
        from public.lotes_materiais_fabrica lmf
        where lmf.material_chave = public.fn_chave_material(v_material)
          and lmf.quantidade_disponivel > 0
        order by lmf.recebido_em, lmf.id
    ) lote;

    return jsonb_build_object(
        'item_requisicao_id', p_item_requisicao_id,
        'material', v_material,
        'rastreabilidade_requisicao', v_rastreabilidade,
        'quantidade_restante_requisicao', greatest(
            v_quantidade_solicitada - v_quantidade_entregue,
            0
        ),
        'quantidade_disponivel', v_quantidade_disponivel,
        'lotes', v_lotes
    );
end;
$$;

-- ============================================================================
-- 11-B. RPC: ENTREGA COM SELEÇÃO EXPLÍCITA DE LOTES DA FÁBRICA
-- ============================================================================

create function public.registrar_entrega_com_fabrica(
    p_item_requisicao_id bigint,
    p_quantidade_total numeric,
    p_lotes jsonb,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_quantidade_solicitada numeric(14, 3);
    v_quantidade_entregue numeric(14, 3);
    v_quantidade_restante numeric(14, 3);
    v_material text;
    v_tipo_requisicao text;
    v_item jsonb;
    v_lote_id bigint;
    v_quantidade_lote numeric(14, 3);
    v_disponivel_lote numeric(14, 3);
    v_material_lote text;
    v_rastreabilidade_lote text;
    v_quantidade_fabrica numeric(14, 3) := 0;
    v_quantidade_nova numeric(14, 3) := 0;
    v_apontamento_fabrica_id bigint;
    v_apontamento_novo_id bigint;
    v_detalhes_fabrica text := '';
    v_observacao_fabrica text;
begin
    if p_quantidade_total is null or p_quantidade_total <= 0 then
        raise exception 'A quantidade entregue deve ser maior que zero.';
    end if;
    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    if p_lotes is null or jsonb_typeof(p_lotes) <> 'array' then
        raise exception 'A seleção de lotes da fábrica é inválida.';
    end if;
    if exists (
        select 1
        from (
            select (item->>'lote_id')::bigint as lote_id, count(*)
            from jsonb_array_elements(p_lotes) item
            where nullif(item->>'lote_id', '') is not null
            group by (item->>'lote_id')::bigint
            having count(*) > 1
        ) duplicado
    ) then
        raise exception 'O mesmo lote da fábrica foi informado mais de uma vez.';
    end if;

    select ir.quantidade, ir.material, ir.tipo_requisicao
    into v_quantidade_solicitada, v_material, v_tipo_requisicao
    from public.itens_requisicao ir
    where ir.id = p_item_requisicao_id
    for update;

    if not found then
        raise exception 'Item de requisição não encontrado.';
    end if;

    if upper(coalesce(v_tipo_requisicao, '')) <> 'EST' then
        raise exception 'Somente itens EST recebem apontamento de entrega.';
    end if;

    v_quantidade_entregue :=
        public.fn_quantidade_entregue_liquida(p_item_requisicao_id);

    v_quantidade_restante := greatest(
        v_quantidade_solicitada - v_quantidade_entregue, 0
    );

    if v_quantidade_restante <= 0 then
        raise exception 'A requisição já está totalmente atendida.';
    end if;
    if p_quantidade_total > v_quantidade_restante then
        raise exception
            'Para usar material da fábrica, a quantidade (%) não pode ser maior que o restante da requisição (%).',
            p_quantidade_total, v_quantidade_restante;
    end if;

    -- Valida e bloqueia explicitamente todos os lotes escolhidos pelo operador.
    -- Neste momento também montamos a observação que ficará no histórico.
    for v_item in
        select value from jsonb_array_elements(p_lotes)
    loop
        v_lote_id := nullif(v_item->>'lote_id', '')::bigint;
        v_quantidade_lote := nullif(v_item->>'quantidade', '')::numeric;

        if v_lote_id is null
           or v_quantidade_lote is null
           or v_quantidade_lote <= 0 then
            raise exception 'Há um lote ou quantidade inválida na seleção da fábrica.';
        end if;

        select
            lmf.quantidade_disponivel,
            lmf.material,
            lmf.rastreabilidade
        into
            v_disponivel_lote,
            v_material_lote,
            v_rastreabilidade_lote
        from public.lotes_materiais_fabrica lmf
        where lmf.id = v_lote_id
        for update;

        if not found then
            raise exception 'Lote de fábrica % não encontrado.', v_lote_id;
        end if;

        if public.fn_chave_material(v_material_lote)
           <> public.fn_chave_material(v_material) then
            raise exception 'O lote % pertence a outro material.', v_lote_id;
        end if;
        if v_quantidade_lote > v_disponivel_lote then
            raise exception
                'Saldo insuficiente no lote %. Disponível: %.',
                v_lote_id, v_disponivel_lote;
        end if;

        v_quantidade_fabrica := v_quantidade_fabrica + v_quantidade_lote;

        if v_detalhes_fabrica <> '' then
            v_detalhes_fabrica := v_detalhes_fabrica || '; ';
        end if;
        v_detalhes_fabrica := v_detalhes_fabrica
            || coalesce(nullif(btrim(v_rastreabilidade_lote), ''), 'SEM RASTREABILIDADE')
            || ': '
            || to_char(v_quantidade_lote, 'FM999999990.###');
    end loop;

    if v_quantidade_fabrica <= 0 then
        raise exception 'Selecione ao menos um lote da fábrica.';
    end if;
    if v_quantidade_fabrica > p_quantidade_total then
        raise exception
            'O total selecionado na fábrica (%) é maior que a quantidade da entrega (%).',
            v_quantidade_fabrica, p_quantidade_total;
    end if;

    v_observacao_fabrica := 'Usado da fábrica | Rastreabilidade(s): ' || v_detalhes_fabrica;
    if nullif(btrim(p_observacao), '') is not null then
        v_observacao_fabrica := v_observacao_fabrica || ' | ' || btrim(p_observacao);
    end if;

    v_quantidade_nova := p_quantidade_total - v_quantidade_fabrica;

    insert into public.apontamentos_entrega (
        item_requisicao_id, quantidade_entregue, quantidade_excedente,
        origem_entrega, usuario, observacao
    )
    values (
        p_item_requisicao_id, v_quantidade_fabrica, 0,
        'FABRICA', btrim(p_usuario), v_observacao_fabrica
    )
    returning id into v_apontamento_fabrica_id;

    for v_item in
        select value from jsonb_array_elements(p_lotes)
    loop
        v_lote_id := (v_item->>'lote_id')::bigint;
        v_quantidade_lote := (v_item->>'quantidade')::numeric;

        update public.lotes_materiais_fabrica
        set quantidade_disponivel = quantidade_disponivel - v_quantidade_lote
        where id = v_lote_id;

        insert into public.consumos_materiais_fabrica (
            lote_material_fabrica_id, apontamento_destino_id,
            quantidade_consumida, quantidade_estornada, usuario
        )
        values (
            v_lote_id, v_apontamento_fabrica_id,
            v_quantidade_lote, 0, btrim(p_usuario)
        );
    end loop;

    -- A parcela complementada pelo almoxarifado continua como um apontamento
    -- NOVO separado. A observação automática de fábrica fica somente no
    -- apontamento FABRICA, evitando afirmar que a parcela NOVA veio de fábrica.
    if v_quantidade_nova > 0 then
        insert into public.apontamentos_entrega (
            item_requisicao_id, quantidade_entregue, quantidade_excedente,
            origem_entrega, usuario, observacao
        )
        values (
            p_item_requisicao_id, v_quantidade_nova, 0,
            'NOVO', btrim(p_usuario), nullif(btrim(p_observacao), '')
        )
        returning id into v_apontamento_novo_id;
    end if;

    return jsonb_build_object(
        'status', 'REGISTRADO_COM_FABRICA',
        'apontamento_fabrica_id', v_apontamento_fabrica_id,
        'apontamento_novo_id', v_apontamento_novo_id,
        'quantidade_fabrica', v_quantidade_fabrica,
        'quantidade_nova', v_quantidade_nova,
        'quantidade_restante',
            greatest(v_quantidade_restante - p_quantidade_total, 0)
    );
end;
$$;

-- ============================================================================
-- 11-C. RPC: INCLUSÃO MANUAL DE MATERIAL NO ESTOQUE DE FÁBRICA
-- ============================================================================

create function public.incluir_material_fabrica_manual(
    p_material text,
    p_rastreabilidade text,
    p_quantidade numeric,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_lote_id bigint;
begin
    if nullif(btrim(p_material), '') is null then
        raise exception 'Informe o material.';
    end if;
    if nullif(btrim(p_rastreabilidade), '') is null then
        raise exception 'Informe a rastreabilidade.';
    end if;
    if p_quantidade is null or p_quantidade <= 0 then
        raise exception 'A quantidade deve ser maior que zero.';
    end if;
    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    insert into public.lotes_materiais_fabrica (
        apontamento_origem_id, origem_lote, observacao_origem,
        material, material_chave, rastreabilidade, rastreabilidade_chave,
        quantidade_inicial, quantidade_disponivel, usuario
    )
    values (
        null, 'MANUAL', nullif(btrim(p_observacao), ''),
        btrim(p_material), public.fn_chave_material(p_material),
        btrim(p_rastreabilidade), public.fn_chave_material(p_rastreabilidade),
        p_quantidade, p_quantidade, btrim(p_usuario)
    )
    returning id into v_lote_id;

    return jsonb_build_object(
        'status', 'INCLUIDO',
        'lote_material_fabrica_id', v_lote_id,
        'quantidade_disponivel', p_quantidade
    );
end;
$$;

-- ============================================================================
-- 11-D. RPC: REQUISIÇÃO MANUAL RM1, RM2, RM3...
-- ============================================================================

create function public.incluir_requisicao_manual(
    p_material text,
    p_quantidade numeric,
    p_usuario text,
    p_dimensao text default null,
    p_rastreabilidade text default null,
    p_localizacao_est text default 'EST',
    p_setor_dest text default null,
    p_peso_bruto_kg numeric default null,
    p_peso_liquido_kg numeric default null,
    p_tipo_material text default 'MANUAL'
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_numero text;
    v_email_id bigint;
    v_item_id bigint;
    v_resumo_id bigint;
begin
    if nullif(btrim(p_material), '') is null then
        raise exception 'Informe o material.';
    end if;
    if p_quantidade is null or p_quantidade <= 0 then
        raise exception 'A quantidade deve ser maior que zero.';
    end if;
    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;
    if p_peso_bruto_kg is not null and p_peso_bruto_kg < 0 then
        raise exception 'O peso bruto não pode ser negativo.';
    end if;
    if p_peso_liquido_kg is not null and p_peso_liquido_kg < 0 then
        raise exception 'O peso líquido não pode ser negativo.';
    end if;

    v_numero := 'RM' || nextval('public.seq_requisicao_manual')::text;

    insert into public.emails_importados (
        hash_arquivo, nome_arquivo, assunto, remetente, recebido_em,
        tipo_requisicao, tipo_material, origem_registro,
        qtd_material_requisicao, qtd_material_baixa,
        peso_bruto_material, peso_liquido_material, importado_por
    )
    values (
        'MANUAL:' || v_numero, v_numero,
        'Requisição manual ' || v_numero, 'LANÇAMENTO MANUAL', now(),
        'EST', coalesce(nullif(btrim(p_tipo_material), ''), 'MANUAL'), 'MANUAL',
        1, 1, coalesce(p_peso_bruto_kg, 0), coalesce(p_peso_liquido_kg, 0),
        btrim(p_usuario)
    )
    returning id into v_email_id;

    insert into public.itens_requisicao (
        email_importado_id, tipo_material, tipo_requisicao, numero_requisicao,
        material, dimensao, quantidade, rastreabilidade, data_requisicao,
        maquina, localizacao_est, setor_dest,
        peso_material_kg, peso_requisitado_kg
    )
    values (
        v_email_id, coalesce(nullif(btrim(p_tipo_material), ''), 'MANUAL'),
        'EST', v_numero, btrim(p_material), nullif(btrim(p_dimensao), ''),
        p_quantidade, nullif(btrim(p_rastreabilidade), ''), current_date,
        'MANUAL', coalesce(nullif(btrim(p_localizacao_est), ''), 'EST'),
        nullif(btrim(p_setor_dest), ''), p_peso_bruto_kg, p_peso_liquido_kg
    )
    returning id into v_item_id;

    insert into public.itens_resumo_totvs (
        email_importado_id, tipo_material, tipo_requisicao,
        numero_requisicao, material, os_so, numero_of,
        peso_material_kg, peso_requisitado_kg
    )
    values (
        v_email_id, coalesce(nullif(btrim(p_tipo_material), ''), 'MANUAL'),
        'EST', v_numero, btrim(p_material), null, null,
        p_peso_bruto_kg, p_peso_liquido_kg
    )
    returning id into v_resumo_id;

    return jsonb_build_object(
        'status', 'CRIADO',
        'numero_requisicao', v_numero,
        'email_importado_id', v_email_id,
        'item_requisicao_id', v_item_id,
        'item_resumo_totvs_id', v_resumo_id
    );
end;
$$;

-- ============================================================================
-- 12. VIEWS DA APLICAÇÃO
-- ============================================================================

create view public.vw_progresso_requisicoes as
select
    ir.id as item_requisicao_id,
    ir.email_importado_id,
    ir.numero_requisicao,
    ir.tipo_material,
    ir.tipo_requisicao,
    ir.material,
    ir.dimensao,

    ir.quantidade as quantidade_solicitada,

    coalesce(movimento.quantidade_entregue, 0)::numeric(14, 3)
        as quantidade_entregue,

    greatest(
        ir.quantidade - coalesce(movimento.quantidade_entregue, 0),
        0
    )::numeric(14, 3) as quantidade_restante,

    case
        when upper(ir.tipo_requisicao) = 'FAB'
            then 'NAO_REQUER_ENTREGA'
        when ir.quantidade - coalesce(movimento.quantidade_entregue, 0) <= 0
            then 'ENTREGUE'
        when coalesce(movimento.quantidade_entregue, 0) > 0
            then 'PARCIAL'
        else 'PENDENTE'
    end as status_entrega,

    ir.rastreabilidade,
    ir.data_requisicao,
    ir.maquina,
    ir.localizacao_est,
    ir.setor_dest,
    ir.peso_material_kg,
    ir.peso_requisitado_kg,

    case
        when upper(ir.tipo_requisicao) = 'EST'
         and ir.quantidade - coalesce(movimento.quantidade_entregue, 0) <= 0
            then movimento.ultima_entrega_em
        else null
    end as concluido_em,

    ie.nome_arquivo as nome_arquivo_email,
    ie.assunto as assunto_email,
    ie.recebido_em as recebido_em_email,
    ie.tipo_material as tipo_material_email

from public.itens_requisicao ir
join public.emails_importados ie
  on ie.id = ir.email_importado_id
left join lateral (
    select
        coalesce(
            sum(
                greatest(
                    ae.quantidade_entregue
                    - coalesce(devolucao.quantidade_devolvida, 0),
                    0
                )
            ),
            0
        ) as quantidade_entregue,
        max(ae.entregue_em) as ultima_entrega_em
    from public.apontamentos_entrega ae
    left join lateral (
        select coalesce(sum(de.quantidade_devolvida), 0)
            as quantidade_devolvida
        from public.devolucoes_entrega de
        where de.apontamento_entrega_id = ae.id
    ) devolucao on true
    where ae.item_requisicao_id = ir.id
) movimento on true;

create view public.vw_pendencias_est_operador as
select *
from public.vw_progresso_requisicoes
where upper(tipo_requisicao) = 'EST'
  and quantidade_restante > 0;

create view public.vw_resumo_totvs as
select *
from public.vw_progresso_requisicoes
where upper(tipo_requisicao) = 'FAB'
   or (
        upper(tipo_requisicao) = 'EST'
        and quantidade_restante <= 0
   );

-- Uma linha por apontamento de entrega.
create view public.vw_historico_entregas as
select
    ae.id as apontamento_entrega_id,
    ir.id as item_requisicao_id,
    ir.email_importado_id,
    ir.numero_requisicao,

    ir.data_requisicao,
    ie.recebido_em as recebido_em_email,
    ae.entregue_em,

    ir.material,
    ir.dimensao,
    ir.quantidade as quantidade_solicitada,

    ae.quantidade_entregue::numeric(14, 3)
        as quantidade_entregue_original,

    coalesce(devolucao.quantidade_devolvida, 0)::numeric(14, 3)
        as quantidade_devolvida,

    greatest(
        ae.quantidade_entregue
        - coalesce(devolucao.quantidade_devolvida, 0),
        0
    )::numeric(14, 3) as quantidade_entregue,

    ae.quantidade_excedente::numeric(14, 3)
        as quantidade_excedente,

    ae.origem_entrega,

    ir.rastreabilidade,
    ir.localizacao_est,
    ir.setor_dest,

    ae.usuario,
    ae.observacao,

    case
        when coalesce(devolucao.quantidade_devolvida, 0) = 0
            then 'ENTREGUE'
        when ae.quantidade_entregue
             - coalesce(devolucao.quantidade_devolvida, 0) <= 0
            then 'DEVOLVIDO'
        else 'DEVOLVIDO_PARCIAL'
    end as status_apontamento,

    devolucao.ultima_devolucao_em

from public.apontamentos_entrega ae
join public.itens_requisicao ir
  on ir.id = ae.item_requisicao_id
join public.emails_importados ie
  on ie.id = ir.email_importado_id
left join lateral (
    select
        coalesce(sum(de.quantidade_devolvida), 0)
            as quantidade_devolvida,
        max(de.devolvido_em) as ultima_devolucao_em
    from public.devolucoes_entrega de
    where de.apontamento_entrega_id = ae.id
) devolucao on true
where upper(ir.tipo_requisicao) = 'EST';

-- Uma linha por devolução realizada.
create view public.vw_historico_devolucoes as
select
    de.id as devolucao_id,
    de.apontamento_entrega_id,
    ir.id as item_requisicao_id,
    ir.numero_requisicao,

    ir.data_requisicao,
    ie.recebido_em as recebido_em_email,
    ae.entregue_em,
    de.devolvido_em,

    ir.material,
    ir.dimensao,

    ae.quantidade_entregue::numeric(14, 3)
        as quantidade_entregue_original,
    de.quantidade_devolvida::numeric(14, 3)
        as quantidade_devolvida,

    ir.rastreabilidade,
    ir.localizacao_est,
    ir.setor_dest,

    de.usuario as operador_devolucao,
    de.observacao as observacao_devolucao,
    ae.usuario as operador_entrega,

    ae.origem_entrega,
    ae.quantidade_excedente::numeric(14, 3)
        as quantidade_excedente

from public.devolucoes_entrega de
join public.apontamentos_entrega ae
  on ae.id = de.apontamento_entrega_id
join public.itens_requisicao ir
  on ir.id = ae.item_requisicao_id
join public.emails_importados ie
  on ie.id = ir.email_importado_id;

-- Tela de consulta dos lotes que ainda possuem saldo.
create view public.vw_materiais_fabrica as
select
    lmf.id as lote_material_fabrica_id,
    lmf.apontamento_origem_id,
    lmf.origem_lote,
    lmf.observacao_origem,
    lmf.recebido_em,

    ir_origem.numero_requisicao as numero_requisicao_origem,
    ir_origem.data_requisicao as data_requisicao_origem,
    ie_origem.recebido_em as recebido_em_requisicao_origem,

    lmf.material,
    lmf.rastreabilidade,
    lmf.quantidade_inicial,
    lmf.quantidade_disponivel,
    lmf.usuario
from public.lotes_materiais_fabrica lmf
left join public.apontamentos_entrega ae_origem
  on ae_origem.id = lmf.apontamento_origem_id
left join public.itens_requisicao ir_origem
  on ir_origem.id = ae_origem.item_requisicao_id
left join public.emails_importados ie_origem
  on ie_origem.id = ir_origem.email_importado_id
where lmf.quantidade_disponivel > 0;

-- ============================================================================
-- 13. PERMISSÕES PARA O CLIENTE SUPABASE
-- ============================================================================

grant usage on schema public to anon, authenticated;

alter table public.emails_importados disable row level security;
alter table public.itens_requisicao disable row level security;
alter table public.itens_resumo_totvs disable row level security;
alter table public.apontamentos_entrega disable row level security;
alter table public.devolucoes_entrega disable row level security;
alter table public.lotes_materiais_fabrica disable row level security;
alter table public.consumos_materiais_fabrica disable row level security;
alter table public.ajustes_materiais_fabrica disable row level security;

revoke all
    on public.emails_importados,
       public.itens_requisicao,
       public.itens_resumo_totvs,
       public.apontamentos_entrega,
       public.devolucoes_entrega,
       public.lotes_materiais_fabrica,
       public.consumos_materiais_fabrica,
       public.ajustes_materiais_fabrica
    from anon, authenticated;

grant select
    on public.vw_progresso_requisicoes,
       public.vw_pendencias_est_operador,
       public.vw_resumo_totvs,
       public.vw_historico_entregas,
       public.vw_historico_devolucoes,
       public.vw_materiais_fabrica
    to anon, authenticated;

-- Remove a permissão automática de execução para papéis não explicitados.
revoke all on function public.importar_email(jsonb, jsonb, jsonb) from public;
revoke all on function public.registrar_entrega(bigint, numeric, text, text) from public;
revoke all on function public.consultar_material_fabrica(bigint) from public;
revoke all on function public.registrar_entrega_material_fabrica(bigint, numeric, text, text) from public;
revoke all on function public.registrar_entrega_mista(bigint, numeric, text, text) from public;
revoke all on function public.ajustar_material_fabrica(bigint, numeric, text, text) from public;
revoke all on function public.devolver_material(bigint, numeric, text, text) from public;
revoke all on function public.registrar_entrega_com_fabrica(bigint, numeric, jsonb, text, text) from public;
revoke all on function public.incluir_material_fabrica_manual(text, text, numeric, text, text) from public;
revoke all on function public.incluir_requisicao_manual(text, numeric, text, text, text, text, text, numeric, numeric, text) from public;

grant execute
    on function public.importar_email(jsonb, jsonb, jsonb),
       public.registrar_entrega(bigint, numeric, text, text),
       public.consultar_material_fabrica(bigint),
       public.registrar_entrega_material_fabrica(bigint, numeric, text, text),
       public.registrar_entrega_mista(bigint, numeric, text, text),
       public.ajustar_material_fabrica(bigint, numeric, text, text),
       public.devolver_material(bigint, numeric, text, text),
       public.registrar_entrega_com_fabrica(bigint, numeric, jsonb, text, text),
       public.incluir_material_fabrica_manual(text, text, numeric, text, text),
       public.incluir_requisicao_manual(text, numeric, text, text, text, text, text, numeric, numeric, text)
    to anon, authenticated;

-- Confirma que a base completa utilizada pela aplicação está instalada.
do $$
begin
    if to_regclass('public.itens_resumo_totvs') is null
       or to_regclass('public.itens_requisicao') is null
       or to_regclass('public.apontamentos_entrega') is null
       or to_regclass('public.devolucoes_entrega') is null
       or to_regclass('public.lotes_materiais_fabrica') is null
       or to_regclass('public.vw_progresso_requisicoes') is null
       or to_regclass('public.vw_historico_entregas') is null
       or to_regprocedure('public.fn_chave_material(text)') is null
       or to_regprocedure('public.fn_quantidade_entregue_liquida(bigint)') is null then
        raise exception
            'A base completa do Gerencial Almox não foi encontrada. Execute primeiro a versão completa do banco com entregas, devoluções e materiais em fábrica.';
    end if;
end;
$$;

-- --------------------------------------------------------------------------
-- 1. TABELA DE AUDITORIA
-- --------------------------------------------------------------------------

create table if not exists public.baixas_resumo_totvs (
    id bigint generated by default as identity primary key,

    item_resumo_totvs_id bigint not null
        references public.itens_resumo_totvs(id)
        on delete cascade,

    baixado_por text not null,
    baixado_em timestamptz not null default now(),

    estornado_por text,
    estornado_em timestamptz,

    constraint ck_baixa_totvs_estorno_completo check (
        (estornado_por is null and estornado_em is null)
        or
        (nullif(btrim(estornado_por), '') is not null and estornado_em is not null)
    )
);

create index if not exists idx_baixas_totvs_item_resumo
    on public.baixas_resumo_totvs(item_resumo_totvs_id);

create index if not exists idx_baixas_totvs_data
    on public.baixas_resumo_totvs(baixado_em desc, id desc);

-- Permite uma única baixa ativa por linha do resumo, mas mantém o histórico
-- de ciclos baixa -> estorno -> nova baixa.
create unique index if not exists uq_baixa_totvs_ativa_item
    on public.baixas_resumo_totvs(item_resumo_totvs_id)
    where estornado_em is null;

-- Índices para o relacionamento lógico entre o resumo e as linhas do operador.
create index if not exists idx_itens_requisicao_import_material_chave
    on public.itens_requisicao(
        email_importado_id,
        public.fn_chave_material(material),
        tipo_requisicao
    );

create index if not exists idx_itens_resumo_import_material_chave
    on public.itens_resumo_totvs(
        email_importado_id,
        public.fn_chave_material(material),
        tipo_requisicao
    );

-- --------------------------------------------------------------------------
-- 2. VIEW: LINHAS APTAS E AINDA NÃO BAIXADAS
-- --------------------------------------------------------------------------

create or replace view public.vw_lancamentos_totvs_pendentes as
select
    rs.id as item_resumo_totvs_id,
    rs.email_importado_id,

    upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')) as tipo,

    rs.numero_requisicao,
    rs.material,
    rs.os_so,
    rs.numero_of,
    coalesce(rs.peso_requisitado_kg, 0)::numeric(14, 3) as peso_kg,

    detalhe.data_requisicao,
    ie.recebido_em as recebido_em_email,

    case
        when upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')) = 'EST'
            then detalhe.entregue_em
        else null
    end as entregue_em,

    case
        when upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')) = 'EST'
            then detalhe.operador
        else null
    end as operador

from public.itens_resumo_totvs rs
join public.emails_importados ie
  on ie.id = rs.email_importado_id

left join lateral (
    select
        count(*)::integer as quantidade_itens,
        min(progresso.data_requisicao) as data_requisicao,
        coalesce(
            bool_and(progresso.quantidade_restante <= 0),
            false
        ) as totalmente_entregue,
        max(progresso.concluido_em) as entregue_em,
        (
            select string_agg(
                distinct btrim(historico.usuario),
                ', '
                order by btrim(historico.usuario)
            )
            from public.vw_historico_entregas historico
            where historico.email_importado_id = rs.email_importado_id
              and public.fn_chave_material(historico.material)
                    = public.fn_chave_material(rs.material)
              and historico.quantidade_entregue > 0
              and nullif(btrim(historico.usuario), '') is not null
        ) as operador
    from public.vw_progresso_requisicoes progresso
    where progresso.email_importado_id = rs.email_importado_id
      and upper(coalesce(progresso.tipo_requisicao, ''))
            = upper(coalesce(rs.tipo_requisicao, rs.tipo_material, ''))
      and public.fn_chave_material(progresso.material)
            = public.fn_chave_material(rs.material)
) detalhe on true

where not exists (
    select 1
    from public.baixas_resumo_totvs baixa
    where baixa.item_resumo_totvs_id = rs.id
      and baixa.estornado_em is null
)
and (
    upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')) = 'FAB'
    or (
        upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')) = 'EST'
        and public.fn_chave_material(rs.material) <> ''
        and detalhe.quantidade_itens > 0
        and detalhe.totalmente_entregue
    )
);

-- --------------------------------------------------------------------------
-- 3. VIEW: BAIXAS ATIVAS
-- --------------------------------------------------------------------------

create or replace view public.vw_baixas_resumo_totvs as
select
    baixa.id as baixa_resumo_totvs_id,
    baixa.item_resumo_totvs_id,
    rs.email_importado_id,

    upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')) as tipo,

    rs.numero_requisicao,
    rs.material,
    coalesce(rs.peso_requisitado_kg, 0)::numeric(14, 3) as peso_kg,

    baixa.baixado_por,
    baixa.baixado_em,

    detalhe.data_requisicao,
    ie.recebido_em as recebido_em_email,

    case
        when upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')) = 'EST'
            then detalhe.entregue_em
        else null
    end as entregue_em,

    case
        when upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')) = 'EST'
            then detalhe.operador
        else null
    end as operador

from public.baixas_resumo_totvs baixa
join public.itens_resumo_totvs rs
  on rs.id = baixa.item_resumo_totvs_id
join public.emails_importados ie
  on ie.id = rs.email_importado_id

left join lateral (
    select
        min(progresso.data_requisicao) as data_requisicao,
        max(progresso.concluido_em) as entregue_em,
        (
            select string_agg(
                distinct btrim(historico.usuario),
                ', '
                order by btrim(historico.usuario)
            )
            from public.vw_historico_entregas historico
            where historico.email_importado_id = rs.email_importado_id
              and public.fn_chave_material(historico.material)
                    = public.fn_chave_material(rs.material)
              and historico.quantidade_entregue > 0
              and nullif(btrim(historico.usuario), '') is not null
        ) as operador
    from public.vw_progresso_requisicoes progresso
    where progresso.email_importado_id = rs.email_importado_id
      and upper(coalesce(progresso.tipo_requisicao, ''))
            = upper(coalesce(rs.tipo_requisicao, rs.tipo_material, ''))
      and public.fn_chave_material(progresso.material)
            = public.fn_chave_material(rs.material)
) detalhe on true

where baixa.estornado_em is null;

-- --------------------------------------------------------------------------
-- 4. RPC: MARCAR UM GRUPO DE LINHAS COMO BAIXADO
-- --------------------------------------------------------------------------

create or replace function public.marcar_baixas_resumo_totvs(
    p_item_resumo_ids jsonb,
    p_baixado_por text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_ids bigint[];
    v_item_resumo_id bigint;
    v_email_importado_id bigint;
    v_tipo_requisicao text;
    v_material text;
    v_numero_requisicao text;
    v_quantidade_itens integer;
    v_totalmente_entregue boolean;
    v_quantidade_baixada integer := 0;
begin
    if nullif(btrim(p_baixado_por), '') is null then
        raise exception 'Informe quem está realizando a baixa.';
    end if;

    if p_item_resumo_ids is null
       or jsonb_typeof(p_item_resumo_ids) <> 'array' then
        raise exception 'A lista de linhas selecionadas é inválida.';
    end if;

    select array_agg(id order by id)
    into v_ids
    from (
        select distinct valor::bigint as id
        from jsonb_array_elements_text(p_item_resumo_ids) as item(valor)
    ) ids;

    if coalesce(array_length(v_ids, 1), 0) = 0 then
        raise exception 'Selecione ao menos uma linha para baixar.';
    end if;

    foreach v_item_resumo_id in array v_ids
    loop
        select
            rs.email_importado_id,
            upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')),
            rs.material,
            rs.numero_requisicao
        into
            v_email_importado_id,
            v_tipo_requisicao,
            v_material,
            v_numero_requisicao
        from public.itens_resumo_totvs rs
        where rs.id = v_item_resumo_id
        for update;

        if not found then
            raise exception
                'A linha de resumo % não foi encontrada.',
                v_item_resumo_id;
        end if;

        if exists (
            select 1
            from public.baixas_resumo_totvs baixa
            where baixa.item_resumo_totvs_id = v_item_resumo_id
              and baixa.estornado_em is null
        ) then
            raise exception
                'A requisição % já possui baixa registrada.',
                coalesce(v_numero_requisicao, v_item_resumo_id::text);
        end if;

        if v_tipo_requisicao = 'EST' then
            if public.fn_chave_material(v_material) = '' then
                raise exception
                    'A linha EST % não possui material válido para relacionar com a entrega.',
                    coalesce(v_numero_requisicao, v_item_resumo_id::text);
            end if;

            -- A mesma linha é bloqueada pelas rotinas de entrega e devolução.
            -- Isso impede que o estado mude enquanto a baixa é conferida.
            perform ir.id
            from public.itens_requisicao ir
            where ir.email_importado_id = v_email_importado_id
              and upper(coalesce(ir.tipo_requisicao, '')) = 'EST'
              and public.fn_chave_material(ir.material)
                    = public.fn_chave_material(v_material)
            order by ir.id
            for update;

            select
                count(*)::integer,
                coalesce(
                    bool_and(
                        ir.quantidade
                        - public.fn_quantidade_entregue_liquida(ir.id)
                        <= 0
                    ),
                    false
                )
            into
                v_quantidade_itens,
                v_totalmente_entregue
            from public.itens_requisicao ir
            where ir.email_importado_id = v_email_importado_id
              and upper(coalesce(ir.tipo_requisicao, '')) = 'EST'
              and public.fn_chave_material(ir.material)
                    = public.fn_chave_material(v_material);

            if v_quantidade_itens = 0 then
                raise exception
                    'Não foi encontrada uma requisição do operador para o material %.',
                    coalesce(v_material, '');
            end if;

            if not v_totalmente_entregue then
                raise exception
                    'O material % ainda não foi totalmente entregue pelos operadores.',
                    coalesce(v_material, '');
            end if;
        elsif v_tipo_requisicao <> 'FAB' then
            raise exception
                'O tipo de estoque da requisição % não é EST nem FAB.',
                coalesce(v_numero_requisicao, v_item_resumo_id::text);
        end if;

        insert into public.baixas_resumo_totvs (
            item_resumo_totvs_id,
            baixado_por
        )
        values (
            v_item_resumo_id,
            btrim(p_baixado_por)
        );

        v_quantidade_baixada := v_quantidade_baixada + 1;
    end loop;

    return jsonb_build_object(
        'status', 'BAIXADO',
        'quantidade_baixada', v_quantidade_baixada
    );
end;
$$;

-- --------------------------------------------------------------------------
-- 5. RPC: ESTORNAR UM GRUPO DE BAIXAS
-- --------------------------------------------------------------------------

create or replace function public.estornar_baixa_resumo_totvs(
    p_baixa_ids jsonb,
    p_estornado_por text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_ids bigint[];
    v_baixa_id bigint;
    v_quantidade_estornada integer := 0;
begin
    if nullif(btrim(p_estornado_por), '') is null then
        raise exception 'Informe quem está realizando o estorno da requisição.';
    end if;

    if p_baixa_ids is null
       or jsonb_typeof(p_baixa_ids) <> 'array' then
        raise exception 'A lista de baixas selecionadas é inválida.';
    end if;

    select array_agg(id order by id)
    into v_ids
    from (
        select distinct valor::bigint as id
        from jsonb_array_elements_text(p_baixa_ids) as item(valor)
    ) ids;

    if coalesce(array_length(v_ids, 1), 0) = 0 then
        raise exception 'Selecione ao menos uma baixa para estornar.';
    end if;

    foreach v_baixa_id in array v_ids
    loop
        perform 1
        from public.baixas_resumo_totvs baixa
        where baixa.id = v_baixa_id
          and baixa.estornado_em is null
        for update;

        if not found then
            raise exception
                'A baixa % não foi encontrada ou já foi estornada.',
                v_baixa_id;
        end if;

        update public.baixas_resumo_totvs
        set
            estornado_por = btrim(p_estornado_por),
            estornado_em = now()
        where id = v_baixa_id;

        v_quantidade_estornada := v_quantidade_estornada + 1;
    end loop;

    return jsonb_build_object(
        'status', 'ESTORNADO',
        'quantidade_estornada', v_quantidade_estornada
    );
end;
$$;

-- --------------------------------------------------------------------------
-- 6. BLOQUEIO DE DEVOLUÇÃO APÓS A BAIXA
--    Mantém integralmente o comportamento atual de devolução e acrescenta
--    somente a validação transacional da baixa.
-- --------------------------------------------------------------------------

create or replace function public.devolver_material(
    p_apontamento_entrega_id bigint,
    p_quantidade numeric,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_quantidade_original numeric(14, 3);
    v_quantidade_excedente numeric(14, 3);
    v_quantidade_ja_devolvida numeric(14, 3);
    v_quantidade_disponivel_devolucao numeric(14, 3);
    v_quantidade_restante_apontamento numeric(14, 3);
    v_origem_entrega text;
    v_devolucao_id bigint;

    v_item_requisicao_id bigint;
    v_email_importado_id bigint;
    v_material text;

    v_a_estornar numeric(14, 3);
    v_estornar numeric(14, 3);
    v_consumo record;
    v_lote record;
begin
    if p_quantidade is null or p_quantidade <= 0 then
        raise exception 'A quantidade devolvida deve ser maior que zero.';
    end if;

    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    select
        ae.quantidade_entregue,
        ae.quantidade_excedente,
        ae.origem_entrega,
        ir.id,
        ir.email_importado_id,
        ir.material
    into
        v_quantidade_original,
        v_quantidade_excedente,
        v_origem_entrega,
        v_item_requisicao_id,
        v_email_importado_id,
        v_material
    from public.apontamentos_entrega ae
    join public.itens_requisicao ir
      on ir.id = ae.item_requisicao_id
    where ae.id = p_apontamento_entrega_id
    for update of ae, ir;

    if not found then
        raise exception 'Apontamento de entrega não encontrado.';
    end if;

    if exists (
        select 1
        from public.baixas_resumo_totvs baixa
        join public.itens_resumo_totvs resumo
          on resumo.id = baixa.item_resumo_totvs_id
        where baixa.estornado_em is null
          and resumo.email_importado_id = v_email_importado_id
          and upper(coalesce(resumo.tipo_requisicao, resumo.tipo_material, '')) = 'EST'
          and public.fn_chave_material(resumo.material)
                = public.fn_chave_material(v_material)
    ) then
        raise exception
            'A devolução não pode ser realizada porque este material já foi baixado no TOTVS.';
    end if;

    select coalesce(sum(de.quantidade_devolvida), 0)
    into v_quantidade_ja_devolvida
    from public.devolucoes_entrega de
    where de.apontamento_entrega_id = p_apontamento_entrega_id;

    v_quantidade_disponivel_devolucao :=
        v_quantidade_original - v_quantidade_ja_devolvida;

    if p_quantidade > v_quantidade_disponivel_devolucao then
        raise exception
            'A quantidade informada (%) é maior que a disponível para devolução (%).',
            p_quantidade,
            v_quantidade_disponivel_devolucao;
    end if;

    insert into public.devolucoes_entrega (
        apontamento_entrega_id,
        quantidade_devolvida,
        usuario,
        observacao
    )
    values (
        p_apontamento_entrega_id,
        p_quantidade,
        btrim(p_usuario),
        nullif(btrim(p_observacao), '')
    )
    returning id into v_devolucao_id;

    v_quantidade_restante_apontamento :=
        v_quantidade_disponivel_devolucao - p_quantidade;

    -- Uma devolução de material reaproveitado retorna aos mesmos lotes.
    if v_origem_entrega = 'FABRICA' then
        v_a_estornar := p_quantidade;

        for v_consumo in
            select
                cmf.id,
                cmf.lote_material_fabrica_id,
                cmf.quantidade_consumida - cmf.quantidade_estornada
                    as quantidade_restauravel
            from public.consumos_materiais_fabrica cmf
            where cmf.apontamento_destino_id = p_apontamento_entrega_id
              and cmf.quantidade_consumida - cmf.quantidade_estornada > 0
            order by cmf.id desc
            for update
        loop
            exit when v_a_estornar <= 0;

            v_estornar := least(
                v_consumo.quantidade_restauravel,
                v_a_estornar
            );

            update public.consumos_materiais_fabrica
            set quantidade_estornada = quantidade_estornada + v_estornar
            where id = v_consumo.id;

            perform 1
            from public.lotes_materiais_fabrica
            where id = v_consumo.lote_material_fabrica_id
            for update;

            update public.lotes_materiais_fabrica
            set quantidade_disponivel = quantidade_disponivel + v_estornar
            where id = v_consumo.lote_material_fabrica_id;

            v_a_estornar := v_a_estornar - v_estornar;
        end loop;

        if v_a_estornar > 0 then
            raise exception
                'Inconsistência no consumo dos lotes. Não foi possível estornar %.',
                v_a_estornar;
        end if;
    end if;

    -- Se a entrega NOVA foi totalmente devolvida, remove da fábrica todo o
    -- excedente dessa entrega que ainda não tinha sido consumido.
    if v_origem_entrega = 'NOVO'
       and v_quantidade_restante_apontamento <= 0
       and v_quantidade_excedente > 0 then
        for v_lote in
            select
                lmf.id,
                lmf.quantidade_disponivel
            from public.lotes_materiais_fabrica lmf
            where lmf.apontamento_origem_id = p_apontamento_entrega_id
              and lmf.quantidade_disponivel > 0
            for update
        loop
            insert into public.ajustes_materiais_fabrica (
                lote_material_fabrica_id,
                quantidade_anterior,
                quantidade_nova,
                diferenca,
                usuario,
                observacao,
                motivo
            )
            values (
                v_lote.id,
                v_lote.quantidade_disponivel,
                0,
                -v_lote.quantidade_disponivel,
                btrim(p_usuario),
                coalesce(
                    nullif(btrim(p_observacao), ''),
                    'Excedente removido após devolução total da entrega.'
                ),
                'DEVOLUCAO_TOTAL_DA_ENTREGA'
            );

            update public.lotes_materiais_fabrica
            set quantidade_disponivel = 0
            where id = v_lote.id;
        end loop;
    end if;

    return jsonb_build_object(
        'status', 'DEVOLVIDO',
        'devolucao_id', v_devolucao_id,
        'apontamento_entrega_id', p_apontamento_entrega_id,
        'quantidade_devolvida', p_quantidade,
        'quantidade_entregue_restante', v_quantidade_restante_apontamento,
        'origem_entrega', v_origem_entrega
    );
end;
$$;

-- --------------------------------------------------------------------------
-- 7. PERMISSÕES
-- --------------------------------------------------------------------------

alter table public.baixas_resumo_totvs disable row level security;

-- A aplicação consulta somente as views e grava somente pelas RPCs.
revoke all on table public.baixas_resumo_totvs from anon, authenticated;

grant select
    on public.vw_lancamentos_totvs_pendentes,
       public.vw_baixas_resumo_totvs
    to anon, authenticated;

revoke all on function public.marcar_baixas_resumo_totvs(jsonb, text) from public;
revoke all on function public.estornar_baixa_resumo_totvs(jsonb, text) from public;
revoke all on function public.devolver_material(bigint, numeric, text, text) from public;

grant execute
    on function public.marcar_baixas_resumo_totvs(jsonb, text),
       public.estornar_baixa_resumo_totvs(jsonb, text),
       public.devolver_material(bigint, numeric, text, text)
    to anon, authenticated;

-- ============================================================================
-- 14. CONTROLE FUNCIONAL DE ACESSO POR USUÁRIO DO WINDOWS
-- ============================================================================
-- Não existe autenticação por senha. A aplicação identifica o usuário usando
-- getpass.getuser() e consulta estas tabelas para montar o menu.

create table public.app_usuarios (
    id bigint generated by default as identity primary key,
    usuario_windows text not null,
    nome_exibicao text not null,
    ativo boolean not null default true,
    administrador boolean not null default false,
    tema text not null default 'Dark'
        check (tema in ('Dark', 'Light', 'System')),
    ultimo_acesso timestamptz,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create unique index ux_app_usuarios_usuario_windows
    on public.app_usuarios (lower(btrim(usuario_windows)));

create table public.app_modulos (
    codigo text primary key,
    nome text not null,
    ordem integer not null default 999,
    ativo boolean not null default true,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table public.app_usuario_modulos (
    usuario_id bigint not null
        references public.app_usuarios(id)
        on delete cascade,
    modulo_codigo text not null
        references public.app_modulos(codigo)
        on delete cascade,
    permitido boolean not null default true,
    criado_em timestamptz not null default now(),
    primary key (usuario_id, modulo_codigo)
);

create table public.app_usuario_preferencias (
    usuario_id bigint not null
        references public.app_usuarios(id)
        on delete cascade,
    modulo_codigo text not null
        references public.app_modulos(codigo)
        on delete cascade,
    preferencias jsonb not null default '{}'::jsonb,
    atualizado_em timestamptz not null default now(),
    primary key (usuario_id, modulo_codigo)
);

create index idx_app_usuario_modulos_modulo
    on public.app_usuario_modulos(modulo_codigo);

create index idx_app_usuario_preferencias_modulo
    on public.app_usuario_preferencias(modulo_codigo);

create function public.app_atualizar_atualizado_em()
returns trigger
language plpgsql
set search_path = public
as $$
begin
    new.atualizado_em := now();
    return new;
end;
$$;

create trigger trg_app_usuarios_atualizado_em
before update on public.app_usuarios
for each row execute function public.app_atualizar_atualizado_em();

create trigger trg_app_modulos_atualizado_em
before update on public.app_modulos
for each row execute function public.app_atualizar_atualizado_em();

create trigger trg_app_usuario_preferencias_atualizado_em
before update on public.app_usuario_preferencias
for each row execute function public.app_atualizar_atualizado_em();

create function public.app_registrar_ultimo_acesso(
    p_usuario_id bigint
)
returns void
language sql
security definer
set search_path = public
as $$
    update public.app_usuarios
       set ultimo_acesso = now()
     where id = p_usuario_id;
$$;

-- Catálogo inicial dos módulos. O carregador também pode sincronizar módulos
-- novos posteriormente, mas estes registros permitem iniciar uma base vazia.
insert into public.app_modulos (codigo, nome, ordem, ativo)
values
    ('importador_emails', 'Importar Requisições', 1, true),
    ('entregas_est', 'Requisições', 2, true),
    ('resumo_requisicoes', 'Resumo de Requisições', 3, true),
    ('materiais_fabrica', 'Em Fábrica', 4, true),
    ('devolucoes_entrega', 'Histórico Devoluções', 5, true),
    ('lancamentos_totvs', 'Baixas TOTVS', 6, true),
    ('historico_baixas_totvs', 'Histórico Baixa', 7, true),
    ('indicadores_apontamentos', 'Indicadores de Entrega', 8, true),
    ('gestao_usuarios', 'Gestão de Usuários', 100, true);

-- ============================================================================
-- CONFIGURAÇÃO OBRIGATÓRIA DO PRIMEIRO ADMINISTRADOR
-- ============================================================================
-- EDITE somente os dois valores abaixo antes de executar o arquivo:
--   v_usuario_admin: resultado de $env:USERNAME no Windows, sem domínio.
--   v_nome_admin: nome que será exibido no aplicativo.
do $configuracao_admin$
declare
    -- Identificação automática utilizada pelo aplicativo (sem domínio e sem nome do computador).
    v_usuario_admin text := 'guilherme.silva';
    v_nome_admin text := 'Guilherme Nery';
begin
    -- Valida somente valores realmente vazios.
    -- Não compare estes campos com os valores cadastrados, pois isso bloquearia
    -- justamente o administrador informado acima.
    if nullif(btrim(v_usuario_admin), '') is null
       or nullif(btrim(v_nome_admin), '') is null then
        raise exception using
            message = 'Informe v_usuario_admin e v_nome_admin antes de executar o SQL.';
    end if;

    insert into public.app_usuarios (
        usuario_windows,
        nome_exibicao,
        ativo,
        administrador,
        tema
    )
    values (
        lower(btrim(v_usuario_admin)),
        btrim(v_nome_admin),
        true,
        true,
        'Dark'
    );
end;
$configuracao_admin$;

-- Sem autenticação por senha, estas tabelas precisam estar disponíveis para a
-- chave pública usada pelo aplicativo. É controle funcional de interface.
alter table public.app_usuarios disable row level security;
alter table public.app_modulos disable row level security;
alter table public.app_usuario_modulos disable row level security;
alter table public.app_usuario_preferencias disable row level security;

grant select, insert, update, delete
    on public.app_usuarios,
       public.app_modulos,
       public.app_usuario_modulos,
       public.app_usuario_preferencias
    to anon, authenticated;

grant usage, select
    on sequence public.app_usuarios_id_seq
    to anon, authenticated;

revoke all on function public.app_registrar_ultimo_acesso(bigint) from public;
grant execute on function public.app_registrar_ultimo_acesso(bigint)
    to anon, authenticated;


-- ============================================================================
-- 15. INDICADORES DOS APONTAMENTOS
-- ============================================================================
-- PESO BRUTO:  Peso Perfil / Peso Chapa da tabela detalhada
--              (itens_requisicao.peso_material_kg).
-- PESO LÍQUIDO: Peso (KG) utilizado na baixa TOTVS
--               (itens_resumo_totvs.peso_requisitado_kg).
-- Os pesos são distribuídos proporcionalmente entre apontamentos parciais para
-- evitar duplicar o peso total de uma mesma requisição.

create view public.vw_indicadores_apontamentos as
with devolucoes as (
    select
        de.apontamento_entrega_id,
        coalesce(sum(de.quantidade_devolvida), 0)::numeric(18, 6)
            as quantidade_devolvida
    from public.devolucoes_entrega de
    group by de.apontamento_entrega_id
),
detalhe_material as (
    select
        ir.email_importado_id,
        upper(coalesce(ir.tipo_requisicao, '')) as tipo_requisicao,
        public.fn_chave_material(ir.material) as material_chave,
        coalesce(sum(ir.quantidade), 0)::numeric(18, 6)
            as quantidade_total_material
    from public.itens_requisicao ir
    group by
        ir.email_importado_id,
        upper(coalesce(ir.tipo_requisicao, '')),
        public.fn_chave_material(ir.material)
),
resumo_totvs_material as (
    select
        rs.email_importado_id,
        upper(coalesce(rs.tipo_requisicao, rs.tipo_material, ''))
            as tipo_requisicao,
        public.fn_chave_material(rs.material) as material_chave,
        coalesce(sum(rs.peso_requisitado_kg), 0)::numeric(18, 6)
            as peso_liquido_total_kg
    from public.itens_resumo_totvs rs
    group by
        rs.email_importado_id,
        upper(coalesce(rs.tipo_requisicao, rs.tipo_material, '')),
        public.fn_chave_material(rs.material)
),
base as (
    select
        ae.id as apontamento_entrega_id,
        ir.id as item_requisicao_id,
        ir.email_importado_id,

        ir.data_requisicao,
        ie.recebido_em as recebido_em_email,
        ae.entregue_em,
        (ae.entregue_em at time zone 'America/Sao_Paulo')::date
            as data_entrega,

        ir.material,
        ir.tipo_requisicao,
        ae.usuario,

        ir.quantidade::numeric(18, 6) as quantidade_solicitada_item,
        greatest(
            ae.quantidade_entregue - coalesce(d.quantidade_devolvida, 0),
            0
        )::numeric(18, 6) as quantidade_entregue_liquida,

        coalesce(ir.peso_material_kg, 0)::numeric(18, 6)
            as peso_bruto_item_kg,
        coalesce(dm.quantidade_total_material, 0)::numeric(18, 6)
            as quantidade_total_material,
        coalesce(rt.peso_liquido_total_kg, 0)::numeric(18, 6)
            as peso_liquido_total_kg

    from public.apontamentos_entrega ae
    join public.itens_requisicao ir
      on ir.id = ae.item_requisicao_id
    join public.emails_importados ie
      on ie.id = ir.email_importado_id
    left join devolucoes d
      on d.apontamento_entrega_id = ae.id
    left join detalhe_material dm
      on dm.email_importado_id = ir.email_importado_id
     and dm.tipo_requisicao = upper(coalesce(ir.tipo_requisicao, ''))
     and dm.material_chave = public.fn_chave_material(ir.material)
    left join resumo_totvs_material rt
      on rt.email_importado_id = ir.email_importado_id
     and rt.tipo_requisicao = upper(coalesce(ir.tipo_requisicao, ''))
     and rt.material_chave = public.fn_chave_material(ir.material)

    where upper(coalesce(ir.tipo_requisicao, '')) = 'EST'
)
select
    base.apontamento_entrega_id,
    base.item_requisicao_id,
    base.email_importado_id,
    base.data_requisicao,
    base.recebido_em_email,
    base.entregue_em,
    base.data_entrega,
    base.material,
    base.tipo_requisicao,
    base.usuario,

    round(
        case
            when base.quantidade_solicitada_item > 0 then
                base.peso_bruto_item_kg
                * base.quantidade_entregue_liquida
                / base.quantidade_solicitada_item
            else 0
        end,
        3
    )::numeric(18, 3) as peso_bruto_entregue_kg,

    round(
        case
            when base.quantidade_total_material > 0 then
                base.peso_liquido_total_kg
                * base.quantidade_entregue_liquida
                / base.quantidade_total_material
            else 0
        end,
        3
    )::numeric(18, 3) as peso_liquido_entregue_kg,

    case
        when coalesce(
            base.recebido_em_email,
            base.data_requisicao::timestamp
                at time zone 'America/Sao_Paulo'
        ) is null then null
        else round(
            greatest(
                extract(epoch from (
                    base.entregue_em
                    - coalesce(
                        base.recebido_em_email,
                        base.data_requisicao::timestamp
                            at time zone 'America/Sao_Paulo'
                    )
                )) / 3600.0,
                0
            )::numeric,
            2
        )
    end as lead_time_horas

from base
where base.quantidade_entregue_liquida > 0;

grant select on public.vw_indicadores_apontamentos
    to anon, authenticated;


-- ============================================================================
-- 16. VALIDAÇÃO FINAL DA INSTALAÇÃO
-- ============================================================================
do $validacao_final$
begin
    if to_regclass('public.emails_importados') is null
       or to_regclass('public.itens_requisicao') is null
       or to_regclass('public.itens_resumo_totvs') is null
       or to_regclass('public.apontamentos_entrega') is null
       or to_regclass('public.devolucoes_entrega') is null
       or to_regclass('public.lotes_materiais_fabrica') is null
       or to_regclass('public.baixas_resumo_totvs') is null
       or to_regclass('public.app_usuarios') is null
       or to_regclass('public.app_modulos') is null
       or to_regclass('public.app_usuario_modulos') is null
       or to_regclass('public.app_usuario_preferencias') is null
       or to_regclass('public.vw_progresso_requisicoes') is null
       or to_regclass('public.vw_lancamentos_totvs_pendentes') is null
       or to_regclass('public.vw_baixas_resumo_totvs') is null
       or to_regclass('public.vw_indicadores_apontamentos') is null
       or to_regprocedure('public.importar_email(jsonb,jsonb,jsonb)') is null
       or to_regprocedure('public.registrar_entrega(bigint,numeric,text,text)') is null
       or to_regprocedure('public.marcar_baixas_resumo_totvs(jsonb,text)') is null
       or to_regprocedure('public.registrar_entrega_com_fabrica(bigint,numeric,jsonb,text,text)') is null
       or to_regprocedure('public.incluir_material_fabrica_manual(text,text,numeric,text,text)') is null
       or to_regprocedure('public.incluir_requisicao_manual(text,numeric,text,text,text,text,text,numeric,numeric,text)') is null
       or to_regprocedure('public.app_registrar_ultimo_acesso(bigint)') is null then
        raise exception
            'Falha na validação final: um ou mais objetos obrigatórios não foram criados.';
    end if;
end;
$validacao_final$;


-- AJUSTES EXCLUSAO / LOTES SEM EQUIVALENCIA 2026-08-19
-- ============================================================================
-- AJUSTES 19/08/2026 - SEM EQUIVALÊNCIA DE MATERIAL
-- 1) Exclusão lógica/auditável de requisições pendentes
-- 2) Histórico de entregas com uma linha por lote de fábrica
-- 3) Devolução direcionada ao lote exibido
-- 4) Observação padrão para inclusão manual em fábrica
-- 5) Restaura correspondência EXATA de material no consumo de fábrica
-- ============================================================================

-- --------------------------------------------------------------------------
-- 1. AUDITORIA DE EXCLUSÕES DE REQUISIÇÕES
-- --------------------------------------------------------------------------
create table if not exists public.exclusoes_requisicao (
    id bigint generated by default as identity primary key,
    item_requisicao_id bigint not null unique
        references public.itens_requisicao(id)
        on delete cascade,
    tipo_requisicao_original text not null default 'EST',
    excluido_por text not null,
    observacao text not null,
    excluido_em timestamptz not null default now()
);

create index if not exists idx_exclusoes_requisicao_data
    on public.exclusoes_requisicao(excluido_em desc, id desc);

alter table public.exclusoes_requisicao disable row level security;
revoke all on table public.exclusoes_requisicao from anon, authenticated;

-- --------------------------------------------------------------------------
-- 2. CONSUMO DE FÁBRICA: SOMENTE MATERIAL EXATO
-- --------------------------------------------------------------------------
-- Se uma versão anterior com equivalência tiver sido aplicada, estas funções
-- restauram o comportamento por fn_chave_material(material), sem fuzzy ou
-- abreviações automáticas.

create or replace function public.consultar_material_fabrica(
    p_item_requisicao_id bigint
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_material text;
    v_rastreabilidade text;
    v_quantidade_solicitada numeric(14, 3);
    v_quantidade_entregue numeric(14, 3);
    v_quantidade_disponivel numeric(14, 3);
    v_lotes jsonb;
begin
    select
        ir.material,
        ir.rastreabilidade,
        ir.quantidade
    into
        v_material,
        v_rastreabilidade,
        v_quantidade_solicitada
    from public.itens_requisicao ir
    where ir.id = p_item_requisicao_id;

    if not found then
        raise exception 'Item de requisição não encontrado.';
    end if;

    v_quantidade_entregue :=
        public.fn_quantidade_entregue_liquida(p_item_requisicao_id);

    select coalesce(sum(lmf.quantidade_disponivel), 0)
    into v_quantidade_disponivel
    from public.lotes_materiais_fabrica lmf
    where lmf.material_chave = public.fn_chave_material(v_material)
      and lmf.quantidade_disponivel > 0;

    select coalesce(
        jsonb_agg(
            jsonb_build_object(
                'lote_id', lote.id,
                'material', lote.material,
                'rastreabilidade', lote.rastreabilidade,
                'quantidade_disponivel', lote.quantidade_disponivel,
                'recebido_em', lote.recebido_em,
                'origem_lote', lote.origem_lote,
                'observacao_origem', lote.observacao_origem
            )
            order by lote.recebido_em, lote.id
        ),
        '[]'::jsonb
    )
    into v_lotes
    from (
        select
            lmf.id,
            lmf.material,
            lmf.rastreabilidade,
            lmf.quantidade_disponivel,
            lmf.recebido_em,
            lmf.origem_lote,
            lmf.observacao_origem
        from public.lotes_materiais_fabrica lmf
        where lmf.material_chave = public.fn_chave_material(v_material)
          and lmf.quantidade_disponivel > 0
        order by lmf.recebido_em, lmf.id
    ) lote;

    return jsonb_build_object(
        'item_requisicao_id', p_item_requisicao_id,
        'material', v_material,
        'rastreabilidade_requisicao', v_rastreabilidade,
        'quantidade_restante_requisicao', greatest(
            v_quantidade_solicitada - v_quantidade_entregue,
            0
        ),
        'quantidade_disponivel', v_quantidade_disponivel,
        'lotes', v_lotes
    );
end;
$$;

create or replace function public.registrar_entrega_com_fabrica(
    p_item_requisicao_id bigint,
    p_quantidade_total numeric,
    p_lotes jsonb,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_quantidade_solicitada numeric(14, 3);
    v_quantidade_entregue numeric(14, 3);
    v_quantidade_restante numeric(14, 3);
    v_material text;
    v_tipo_requisicao text;
    v_item jsonb;
    v_lote_id bigint;
    v_quantidade_lote numeric(14, 3);
    v_disponivel_lote numeric(14, 3);
    v_material_lote text;
    v_rastreabilidade_lote text;
    v_quantidade_fabrica numeric(14, 3) := 0;
    v_quantidade_nova numeric(14, 3) := 0;
    v_apontamento_fabrica_id bigint;
    v_apontamento_novo_id bigint;
    v_detalhes_fabrica text := '';
    v_observacao_fabrica text;
begin
    if p_quantidade_total is null or p_quantidade_total <= 0 then
        raise exception 'A quantidade entregue deve ser maior que zero.';
    end if;
    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    if p_lotes is null or jsonb_typeof(p_lotes) <> 'array' then
        raise exception 'A seleção de lotes da fábrica é inválida.';
    end if;
    if exists (
        select 1
        from (
            select (item->>'lote_id')::bigint as lote_id, count(*)
            from jsonb_array_elements(p_lotes) item
            where nullif(item->>'lote_id', '') is not null
            group by (item->>'lote_id')::bigint
            having count(*) > 1
        ) duplicado
    ) then
        raise exception 'O mesmo lote da fábrica foi informado mais de uma vez.';
    end if;

    select ir.quantidade, ir.material, ir.tipo_requisicao
    into v_quantidade_solicitada, v_material, v_tipo_requisicao
    from public.itens_requisicao ir
    where ir.id = p_item_requisicao_id
    for update;

    if not found then
        raise exception 'Item de requisição não encontrado.';
    end if;

    if upper(coalesce(v_tipo_requisicao, '')) <> 'EST' then
        raise exception 'Somente itens EST recebem apontamento de entrega.';
    end if;

    v_quantidade_entregue :=
        public.fn_quantidade_entregue_liquida(p_item_requisicao_id);

    v_quantidade_restante := greatest(
        v_quantidade_solicitada - v_quantidade_entregue, 0
    );

    if v_quantidade_restante <= 0 then
        raise exception 'A requisição já está totalmente atendida.';
    end if;
    if p_quantidade_total > v_quantidade_restante then
        raise exception
            'Para usar material da fábrica, a quantidade (%) não pode ser maior que o restante da requisição (%).',
            p_quantidade_total, v_quantidade_restante;
    end if;

    -- Valida e bloqueia explicitamente todos os lotes escolhidos pelo operador.
    -- Neste momento também montamos a observação que ficará no histórico.
    for v_item in
        select value from jsonb_array_elements(p_lotes)
    loop
        v_lote_id := nullif(v_item->>'lote_id', '')::bigint;
        v_quantidade_lote := nullif(v_item->>'quantidade', '')::numeric;

        if v_lote_id is null
           or v_quantidade_lote is null
           or v_quantidade_lote <= 0 then
            raise exception 'Há um lote ou quantidade inválida na seleção da fábrica.';
        end if;

        select
            lmf.quantidade_disponivel,
            lmf.material,
            lmf.rastreabilidade
        into
            v_disponivel_lote,
            v_material_lote,
            v_rastreabilidade_lote
        from public.lotes_materiais_fabrica lmf
        where lmf.id = v_lote_id
        for update;

        if not found then
            raise exception 'Lote de fábrica % não encontrado.', v_lote_id;
        end if;

        if public.fn_chave_material(v_material_lote)
           <> public.fn_chave_material(v_material) then
            raise exception 'O lote % pertence a outro material.', v_lote_id;
        end if;
        if v_quantidade_lote > v_disponivel_lote then
            raise exception
                'Saldo insuficiente no lote %. Disponível: %.',
                v_lote_id, v_disponivel_lote;
        end if;

        v_quantidade_fabrica := v_quantidade_fabrica + v_quantidade_lote;

        if v_detalhes_fabrica <> '' then
            v_detalhes_fabrica := v_detalhes_fabrica || '; ';
        end if;
        v_detalhes_fabrica := v_detalhes_fabrica
            || coalesce(nullif(btrim(v_rastreabilidade_lote), ''), 'SEM RASTREABILIDADE')
            || ': '
            || to_char(v_quantidade_lote, 'FM999999990.###');
    end loop;

    if v_quantidade_fabrica <= 0 then
        raise exception 'Selecione ao menos um lote da fábrica.';
    end if;
    if v_quantidade_fabrica > p_quantidade_total then
        raise exception
            'O total selecionado na fábrica (%) é maior que a quantidade da entrega (%).',
            v_quantidade_fabrica, p_quantidade_total;
    end if;

    v_observacao_fabrica := 'Usado da fábrica | Rastreabilidade(s): ' || v_detalhes_fabrica;
    if nullif(btrim(p_observacao), '') is not null then
        v_observacao_fabrica := v_observacao_fabrica || ' | ' || btrim(p_observacao);
    end if;

    v_quantidade_nova := p_quantidade_total - v_quantidade_fabrica;

    insert into public.apontamentos_entrega (
        item_requisicao_id, quantidade_entregue, quantidade_excedente,
        origem_entrega, usuario, observacao
    )
    values (
        p_item_requisicao_id, v_quantidade_fabrica, 0,
        'FABRICA', btrim(p_usuario), v_observacao_fabrica
    )
    returning id into v_apontamento_fabrica_id;

    for v_item in
        select value from jsonb_array_elements(p_lotes)
    loop
        v_lote_id := (v_item->>'lote_id')::bigint;
        v_quantidade_lote := (v_item->>'quantidade')::numeric;

        update public.lotes_materiais_fabrica
        set quantidade_disponivel = quantidade_disponivel - v_quantidade_lote
        where id = v_lote_id;

        insert into public.consumos_materiais_fabrica (
            lote_material_fabrica_id, apontamento_destino_id,
            quantidade_consumida, quantidade_estornada, usuario
        )
        values (
            v_lote_id, v_apontamento_fabrica_id,
            v_quantidade_lote, 0, btrim(p_usuario)
        );
    end loop;

    -- A parcela complementada pelo almoxarifado continua como um apontamento
    -- NOVO separado. A observação automática de fábrica fica somente no
    -- apontamento FABRICA, evitando afirmar que a parcela NOVA veio de fábrica.
    if v_quantidade_nova > 0 then
        insert into public.apontamentos_entrega (
            item_requisicao_id, quantidade_entregue, quantidade_excedente,
            origem_entrega, usuario, observacao
        )
        values (
            p_item_requisicao_id, v_quantidade_nova, 0,
            'NOVO', btrim(p_usuario), nullif(btrim(p_observacao), '')
        )
        returning id into v_apontamento_novo_id;
    end if;

    return jsonb_build_object(
        'status', 'REGISTRADO_COM_FABRICA',
        'apontamento_fabrica_id', v_apontamento_fabrica_id,
        'apontamento_novo_id', v_apontamento_novo_id,
        'quantidade_fabrica', v_quantidade_fabrica,
        'quantidade_nova', v_quantidade_nova,
        'quantidade_restante',
            greatest(v_quantidade_restante - p_quantidade_total, 0)
    );
end;
$$;

-- Remove vestígios da versão de equivalência, caso ela tenha sido aplicada.
drop index if exists public.idx_lotes_fabrica_material_equivalencia;
drop function if exists public.fn_chave_equivalencia_material(text);

-- --------------------------------------------------------------------------
-- 5. INCLUSÃO MANUAL: OBSERVAÇÃO PADRÃO
-- --------------------------------------------------------------------------
create or replace function public.incluir_material_fabrica_manual(
    p_material text,
    p_rastreabilidade text,
    p_quantidade numeric,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_lote_id bigint;
    v_observacao text;
begin
    if nullif(btrim(p_material), '') is null then
        raise exception 'Informe o material.';
    end if;
    if nullif(btrim(p_rastreabilidade), '') is null then
        raise exception 'Informe a rastreabilidade.';
    end if;
    if p_quantidade is null or p_quantidade <= 0 then
        raise exception 'A quantidade deve ser maior que zero.';
    end if;
    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    v_observacao := coalesce(
        nullif(btrim(p_observacao), ''),
        'Inclusão manual'
    );

    insert into public.lotes_materiais_fabrica (
        apontamento_origem_id, origem_lote, observacao_origem,
        material, material_chave, rastreabilidade, rastreabilidade_chave,
        quantidade_inicial, quantidade_disponivel, usuario
    )
    values (
        null, 'MANUAL', v_observacao,
        btrim(p_material), public.fn_chave_material(p_material),
        btrim(p_rastreabilidade), public.fn_chave_material(p_rastreabilidade),
        p_quantidade, p_quantidade, btrim(p_usuario)
    )
    returning id into v_lote_id;

    return jsonb_build_object(
        'status', 'INCLUIDO',
        'lote_material_fabrica_id', v_lote_id,
        'quantidade_disponivel', p_quantidade,
        'observacao', v_observacao
    );
end;
$$;

-- --------------------------------------------------------------------------
-- 6. EXCLUSÃO LÓGICA DA REQUISIÇÃO
-- --------------------------------------------------------------------------
create or replace function public.excluir_requisicao(
    p_item_requisicao_id bigint,
    p_usuario text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_tipo text;
    v_email_id bigint;
    v_material text;
    v_numero text;
    v_observacao text;
    v_exclusao_id bigint;
begin
    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável pela exclusão.';
    end if;

    select
        ir.tipo_requisicao,
        ir.email_importado_id,
        ir.material,
        ir.numero_requisicao
    into
        v_tipo,
        v_email_id,
        v_material,
        v_numero
    from public.itens_requisicao ir
    where ir.id = p_item_requisicao_id
    for update;

    if not found then
        raise exception 'Requisição não encontrada.';
    end if;

    if upper(coalesce(v_tipo, '')) = 'EXCLUIDA' then
        raise exception 'Esta requisição já foi excluída.';
    end if;

    if upper(coalesce(v_tipo, '')) <> 'EST' then
        raise exception 'Somente requisições EST pendentes podem ser excluídas por esta tela.';
    end if;

    -- Se ainda existe quantidade líquida entregue, a exclusão é bloqueada.
    -- O operador deve devolver o que foi entregue antes de excluir a requisição.
    if public.fn_quantidade_entregue_liquida(p_item_requisicao_id) > 0 then
        raise exception
            'Esta requisição possui material entregue. Faça a devolução total antes de excluí-la.';
    end if;

    -- Não permite excluir depois que a linha correspondente já foi baixada.
    if exists (
        select 1
        from public.baixas_resumo_totvs baixa
        join public.itens_resumo_totvs resumo
          on resumo.id = baixa.item_resumo_totvs_id
        where baixa.estornado_em is null
          and resumo.email_importado_id = v_email_id
          and upper(coalesce(resumo.tipo_requisicao, resumo.tipo_material, '')) = 'EST'
          and public.fn_chave_material(resumo.material)
                = public.fn_chave_material(v_material)
    ) then
        raise exception
            'Esta requisição não pode ser excluída porque o material já possui baixa ativa no TOTVS.';
    end if;

    v_observacao :=
        'Exclusão em '
        || to_char(now() at time zone 'America/Sao_Paulo', 'DD/MM/YYYY HH24:MI');

    insert into public.exclusoes_requisicao (
        item_requisicao_id,
        tipo_requisicao_original,
        excluido_por,
        observacao
    )
    values (
        p_item_requisicao_id,
        v_tipo,
        btrim(p_usuario),
        v_observacao
    )
    returning id into v_exclusao_id;

    -- O registro continua no banco para auditoria, mas sai de todos os fluxos EST.
    update public.itens_requisicao
    set tipo_requisicao = 'EXCLUIDA'
    where id = p_item_requisicao_id;

    return jsonb_build_object(
        'status', 'EXCLUIDA',
        'exclusao_id', v_exclusao_id,
        'item_requisicao_id', p_item_requisicao_id,
        'numero_requisicao', v_numero,
        'observacao', v_observacao
    );
end;
$$;

-- --------------------------------------------------------------------------
-- 7. DEVOLUÇÃO DIRECIONADA A UM LOTE DA FÁBRICA
-- --------------------------------------------------------------------------
create or replace function public.devolver_material_lote_fabrica(
    p_consumo_material_fabrica_id bigint,
    p_quantidade numeric,
    p_usuario text,
    p_observacao text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
    v_apontamento_id bigint;
    v_lote_id bigint;
    v_consumida numeric(14, 3);
    v_estornada numeric(14, 3);
    v_disponivel numeric(14, 3);
    v_email_id bigint;
    v_material text;
    v_rastreabilidade text;
    v_devolucao_id bigint;
begin
    if p_quantidade is null or p_quantidade <= 0 then
        raise exception 'A quantidade devolvida deve ser maior que zero.';
    end if;
    if nullif(btrim(p_usuario), '') is null then
        raise exception 'Informe o usuário responsável.';
    end if;

    select
        cmf.apontamento_destino_id,
        cmf.lote_material_fabrica_id,
        cmf.quantidade_consumida,
        cmf.quantidade_estornada,
        ir.email_importado_id,
        ir.material,
        lmf.rastreabilidade
    into
        v_apontamento_id,
        v_lote_id,
        v_consumida,
        v_estornada,
        v_email_id,
        v_material,
        v_rastreabilidade
    from public.consumos_materiais_fabrica cmf
    join public.apontamentos_entrega ae
      on ae.id = cmf.apontamento_destino_id
    join public.itens_requisicao ir
      on ir.id = ae.item_requisicao_id
    join public.lotes_materiais_fabrica lmf
      on lmf.id = cmf.lote_material_fabrica_id
    where cmf.id = p_consumo_material_fabrica_id
      and ae.origem_entrega = 'FABRICA'
    for update of cmf, ae, ir, lmf;

    if not found then
        raise exception 'Consumo do lote de fábrica não encontrado.';
    end if;

    v_disponivel := v_consumida - v_estornada;
    if p_quantidade > v_disponivel then
        raise exception
            'A quantidade informada (%) é maior que a disponível neste lote (%).',
            p_quantidade, v_disponivel;
    end if;

    if exists (
        select 1
        from public.baixas_resumo_totvs baixa
        join public.itens_resumo_totvs resumo
          on resumo.id = baixa.item_resumo_totvs_id
        where baixa.estornado_em is null
          and resumo.email_importado_id = v_email_id
          and upper(coalesce(resumo.tipo_requisicao, resumo.tipo_material, '')) = 'EST'
          and public.fn_chave_material(resumo.material)
                = public.fn_chave_material(v_material)
    ) then
        raise exception
            'A devolução não pode ser realizada porque este material já foi baixado no TOTVS.';
    end if;

    insert into public.devolucoes_entrega (
        apontamento_entrega_id,
        quantidade_devolvida,
        usuario,
        observacao
    )
    values (
        v_apontamento_id,
        p_quantidade,
        btrim(p_usuario),
        coalesce(
            nullif(btrim(p_observacao), ''),
            'Devolução do lote de fábrica ' || coalesce(v_rastreabilidade, '')
        )
    )
    returning id into v_devolucao_id;

    update public.consumos_materiais_fabrica
    set quantidade_estornada = quantidade_estornada + p_quantidade
    where id = p_consumo_material_fabrica_id;

    update public.lotes_materiais_fabrica
    set quantidade_disponivel = quantidade_disponivel + p_quantidade
    where id = v_lote_id;

    return jsonb_build_object(
        'status', 'DEVOLVIDO_LOTE_FABRICA',
        'devolucao_id', v_devolucao_id,
        'apontamento_entrega_id', v_apontamento_id,
        'consumo_material_fabrica_id', p_consumo_material_fabrica_id,
        'quantidade_devolvida', p_quantidade,
        'quantidade_entregue_restante', v_disponivel - p_quantidade,
        'rastreabilidade', v_rastreabilidade
    );
end;
$$;

-- --------------------------------------------------------------------------
-- 8. HISTÓRICO DE ENTREGAS: UMA LINHA POR LOTE DE FÁBRICA
-- --------------------------------------------------------------------------
-- Mantém todas as colunas antigas na mesma ordem e apenas acrescenta os
-- identificadores do lote/consumo ao final.
create or replace view public.vw_historico_entregas as
select
    ae.id as apontamento_entrega_id,
    ir.id as item_requisicao_id,
    ir.email_importado_id,
    ir.numero_requisicao,

    ir.data_requisicao,
    ie.recebido_em as recebido_em_email,
    ae.entregue_em,

    ir.material,
    ir.dimensao,
    ir.quantidade as quantidade_solicitada,

    case
        when ae.origem_entrega = 'FABRICA'
            then coalesce(cmf.quantidade_consumida, 0)
        else ae.quantidade_entregue
    end::numeric(14, 3) as quantidade_entregue_original,

    case
        when ae.origem_entrega = 'FABRICA'
            then coalesce(cmf.quantidade_estornada, 0)
        else coalesce(devolucao.quantidade_devolvida, 0)
    end::numeric(14, 3) as quantidade_devolvida,

    greatest(
        case
            when ae.origem_entrega = 'FABRICA'
                then coalesce(cmf.quantidade_consumida, 0)
                     - coalesce(cmf.quantidade_estornada, 0)
            else ae.quantidade_entregue
                 - coalesce(devolucao.quantidade_devolvida, 0)
        end,
        0
    )::numeric(14, 3) as quantidade_entregue,

    case
        when ae.origem_entrega = 'FABRICA' then 0
        else ae.quantidade_excedente
    end::numeric(14, 3) as quantidade_excedente,

    ae.origem_entrega,

    case
        when ae.origem_entrega = 'FABRICA'
            then coalesce(lmf.rastreabilidade, ir.rastreabilidade)
        else ir.rastreabilidade
    end as rastreabilidade,

    ir.localizacao_est,
    ir.setor_dest,

    ae.usuario,

    case
        when ae.origem_entrega = 'FABRICA' then
            'Usado da fábrica | Rastreabilidade: '
            || coalesce(nullif(btrim(lmf.rastreabilidade), ''), 'SEM RASTREABILIDADE')
            || case
                when nullif(btrim(lmf.observacao_origem), '') is not null
                    then ' | ' || btrim(lmf.observacao_origem)
                else ''
               end
        else ae.observacao
    end as observacao,

    case
        when (
            case
                when ae.origem_entrega = 'FABRICA'
                    then coalesce(cmf.quantidade_estornada, 0)
                else coalesce(devolucao.quantidade_devolvida, 0)
            end
        ) = 0 then 'ENTREGUE'
        when greatest(
            case
                when ae.origem_entrega = 'FABRICA'
                    then coalesce(cmf.quantidade_consumida, 0)
                         - coalesce(cmf.quantidade_estornada, 0)
                else ae.quantidade_entregue
                     - coalesce(devolucao.quantidade_devolvida, 0)
            end,
            0
        ) <= 0 then 'DEVOLVIDO'
        else 'DEVOLVIDO_PARCIAL'
    end as status_apontamento,

    devolucao.ultima_devolucao_em,

    -- Novas colunas, adicionadas ao final para não quebrar consumidores antigos.
    (
        ae.id::text || ':' || coalesce(cmf.id::text, '0')
    ) as historico_entrega_id,
    cmf.id as consumo_material_fabrica_id,
    lmf.id as lote_material_fabrica_id,
    lmf.material as material_lote_fabrica,
    lmf.observacao_origem as observacao_lote_fabrica

from public.apontamentos_entrega ae
join public.itens_requisicao ir
  on ir.id = ae.item_requisicao_id
join public.emails_importados ie
  on ie.id = ir.email_importado_id
left join public.consumos_materiais_fabrica cmf
  on ae.origem_entrega = 'FABRICA'
 and cmf.apontamento_destino_id = ae.id
left join public.lotes_materiais_fabrica lmf
  on lmf.id = cmf.lote_material_fabrica_id
left join lateral (
    select
        coalesce(sum(de.quantidade_devolvida), 0)
            as quantidade_devolvida,
        max(de.devolvido_em) as ultima_devolucao_em
    from public.devolucoes_entrega de
    where de.apontamento_entrega_id = ae.id
) devolucao on true
where upper(ir.tipo_requisicao) = 'EST';

-- --------------------------------------------------------------------------
-- 9. HISTÓRICO DE DEVOLUÇÕES TAMBÉM RECEBE EXCLUSÕES
-- --------------------------------------------------------------------------
create or replace view public.vw_historico_devolucoes as
select
    de.id as devolucao_id,
    de.apontamento_entrega_id,
    ir.id as item_requisicao_id,
    ir.numero_requisicao,

    ir.data_requisicao,
    ie.recebido_em as recebido_em_email,
    ae.entregue_em,
    de.devolvido_em,

    ir.material,
    ir.dimensao,
    ae.quantidade_entregue::numeric(14, 3)
        as quantidade_entregue_original,
    de.quantidade_devolvida::numeric(14, 3)
        as quantidade_devolvida,

    ir.rastreabilidade,
    ir.localizacao_est,
    ir.setor_dest,

    de.usuario as operador_devolucao,
    de.observacao as observacao_devolucao,
    ae.usuario as operador_entrega,

    ae.origem_entrega,
    ae.quantidade_excedente::numeric(14, 3)
        as quantidade_excedente,
    'DEVOLUCAO'::text as tipo_evento

from public.devolucoes_entrega de
join public.apontamentos_entrega ae
  on ae.id = de.apontamento_entrega_id
join public.itens_requisicao ir
  on ir.id = ae.item_requisicao_id
join public.emails_importados ie
  on ie.id = ir.email_importado_id

union all

select
    -ex.id as devolucao_id,
    null::bigint as apontamento_entrega_id,
    ir.id as item_requisicao_id,
    ir.numero_requisicao,

    ir.data_requisicao,
    ie.recebido_em as recebido_em_email,
    null::timestamptz as entregue_em,
    ex.excluido_em as devolvido_em,

    ir.material,
    ir.dimensao,
    0::numeric(14, 3) as quantidade_entregue_original,
    0::numeric(14, 3) as quantidade_devolvida,

    ir.rastreabilidade,
    ir.localizacao_est,
    ir.setor_dest,

    ex.excluido_por as operador_devolucao,
    ex.observacao as observacao_devolucao,
    null::text as operador_entrega,

    'EXCLUSAO'::text as origem_entrega,
    0::numeric(14, 3) as quantidade_excedente,
    'EXCLUSAO'::text as tipo_evento

from public.exclusoes_requisicao ex
join public.itens_requisicao ir
  on ir.id = ex.item_requisicao_id
join public.emails_importados ie
  on ie.id = ir.email_importado_id;

-- --------------------------------------------------------------------------
-- 7. PERMISSÕES
-- --------------------------------------------------------------------------
revoke all on function public.excluir_requisicao(bigint, text) from public;
revoke all on function public.devolver_material_lote_fabrica(bigint, numeric, text, text) from public;
revoke all on function public.consultar_material_fabrica(bigint) from public;
revoke all on function public.registrar_entrega_com_fabrica(bigint, numeric, jsonb, text, text) from public;
revoke all on function public.incluir_material_fabrica_manual(text, text, numeric, text, text) from public;

grant execute
    on function public.excluir_requisicao(bigint, text),
       public.devolver_material_lote_fabrica(bigint, numeric, text, text),
       public.consultar_material_fabrica(bigint),
       public.registrar_entrega_com_fabrica(bigint, numeric, jsonb, text, text),
       public.incluir_material_fabrica_manual(text, text, numeric, text, text)
    to anon, authenticated;

grant select
    on public.vw_historico_entregas,
       public.vw_historico_devolucoes
    to anon, authenticated;

commit;
