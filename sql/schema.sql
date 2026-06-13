create table if not exists perfis (
  id bigserial primary key,
  nome varchar(60) unique not null,
  descricao text
);

create table if not exists zonas_eleitorais (
  id bigserial primary key,
  numero integer unique not null,
  tribunal_sigla varchar(20) default 'TRE-BA',
  uf varchar(2) default 'BA',
  municipio_sede varchar(140),
  horario_atendimento varchar(120),
  endereco text,
  email varchar(180),
  telefone varchar(120),
  whatsapp varchar(120),
  chefe_cartorio varchar(180),
  juiz_eleitoral varchar(180),
  fonte_url text,
  municipios_abrangidos text,
  ativa boolean default true,
  criado_em timestamp default now(),
  atualizado_em timestamp default now()
);

create table if not exists municipios_zona (
  id bigserial primary key,
  zona_eleitoral_id bigint not null references zonas_eleitorais(id) on delete cascade,
  municipio varchar(160) not null,
  sede boolean default false,
  unique(zona_eleitoral_id, municipio)
);

create table if not exists usuarios (
  id bigserial primary key,
  nome varchar(180) not null,
  email varchar(180) unique not null,
  cpf varchar(30) unique,
  senha_hash varchar(255) not null,
  perfil_id bigint not null references perfis(id),
  zona_eleitoral_id bigint references zonas_eleitorais(id),
  secao_operador varchar(40) default 'CRE-BA',
  ativo boolean default true,
  validado boolean default true,
  token_validacao varchar(255),
  token_recuperacao varchar(255),
  token_recuperacao_expira_em timestamp,
  ultimo_login timestamp,
  criado_em timestamp default now(),
  atualizado_em timestamp default now()
);

create table if not exists itens_monitoramento (
  id bigserial primary key,
  grupo varchar(120) not null,
  descricao text not null,
  responsavel_origem varchar(180),
  frequencia varchar(80) not null default 'mensal',
  exige_evidencia boolean default false,
  criticidade varchar(30) default 'media',
  ativo boolean default true,
  criado_em timestamp default now(),
  atualizado_em timestamp default now(),
  unique(grupo, descricao)
);

create table if not exists ciclos_monitoramento (
  id bigserial primary key,
  periodo_inicio date not null,
  periodo_fim date not null,
  tipo_periodicidade varchar(40) not null,
  status varchar(30) default 'aberto',
  criado_em timestamp default now(),
  unique(periodo_inicio, periodo_fim, tipo_periodicidade)
);

create table if not exists tarefas_zona (
  id bigserial primary key,
  zona_eleitoral_id bigint not null references zonas_eleitorais(id) on delete cascade,
  item_monitoramento_id bigint not null references itens_monitoramento(id) on delete cascade,
  ciclo_id bigint not null references ciclos_monitoramento(id) on delete cascade,
  prazo date not null,
  status varchar(40) default 'pendente',
  observacao_corregedoria text,
  criado_em timestamp default now(),
  atualizado_em timestamp default now(),
  unique(zona_eleitoral_id, item_monitoramento_id, ciclo_id)
);

create table if not exists respostas (
  id bigserial primary key,
  tarefa_zona_id bigint not null references tarefas_zona(id) on delete cascade,
  usuario_id bigint not null references usuarios(id),
  status varchar(40) not null,
  observacao text,
  justificativa text,
  evidencia_url text,
  enviado_em timestamp default now()
);

create table if not exists validacoes_corregedoria (
  id bigserial primary key,
  resposta_id bigint not null references respostas(id) on delete cascade,
  usuario_corregedoria_id bigint not null references usuarios(id),
  status_validacao varchar(40) not null,
  observacao text,
  validado_em timestamp default now()
);

create table if not exists comentarios_tarefa (
  id bigserial primary key,
  tarefa_zona_id bigint not null references tarefas_zona(id) on delete cascade,
  comentario text not null,
  autor_usuario_id bigint references usuarios(id),
  autor_nome varchar(180),
  autor_email varchar(180),
  criado_em timestamp default now()
);

create table if not exists anexos_tarefa (
  id bigserial primary key,
  tarefa_zona_id bigint not null references tarefas_zona(id) on delete cascade,
  nome_arquivo varchar(255),
  tipo_arquivo varchar(40) default 'link',
  url_arquivo text,
  enviado_por_usuario_id bigint references usuarios(id),
  enviado_por_nome varchar(180),
  enviado_por_email varchar(180),
  criado_em timestamp default now()
);

create table if not exists logs_auditoria (
  id bigserial primary key,
  usuario_id bigint references usuarios(id),
  usuario_nome varchar(180),
  usuario_email varchar(180),
  acao varchar(100) not null,
  entidade varchar(100) not null,
  entidade_id bigint,
  campo varchar(100),
  valor_anterior text,
  valor_novo text,
  detalhe text,
  ip varchar(80),
  criado_em timestamp default now()
);

create table if not exists backups_registros (
  id bigserial primary key,
  nome_arquivo varchar(255),
  tipo varchar(40),
  quantidade_registros integer default 0,
  gerado_por_usuario_id bigint references usuarios(id),
  gerado_por_nome varchar(180),
  gerado_por_email varchar(180),
  hash_sha256 varchar(80),
  criado_em timestamp default now()
);

create table if not exists configuracoes_sistema (
  chave varchar(100) primary key,
  valor text,
  atualizado_em timestamp default now()
);

create index if not exists idx_zonas_numero on zonas_eleitorais(numero);
create index if not exists idx_zonas_tribunal on zonas_eleitorais(tribunal_sigla);
create index if not exists idx_municipios_zona_municipio on municipios_zona(municipio);
create index if not exists idx_tarefas_status on tarefas_zona(status);
create index if not exists idx_tarefas_prazo on tarefas_zona(prazo);
create index if not exists idx_itens_grupo on itens_monitoramento(grupo);
create index if not exists idx_respostas_tarefa on respostas(tarefa_zona_id);
create index if not exists idx_auditoria_entidade on logs_auditoria(entidade, entidade_id);
