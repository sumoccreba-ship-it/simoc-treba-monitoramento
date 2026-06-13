# SIMOC-BA - Monitoramento Cartorário TRE-BA

Versão Streamlit + Supabase/PostgreSQL do Sistema de Monitoramento Cartorário das Zonas Eleitorais da Bahia.

Esta versão foi ampliada com base no padrão funcional do arquivo `app_siga_cor_fase2_tabelas.py`: cabeçalho com logo da Corregedoria, cadastro/validação/recuperação de usuários, backup/restauração, relatórios PDF/Excel, auditoria/histórico, comentários e anexos por tarefa, e parâmetros de zonas.

## Principais recursos

- Relação-base das Zonas Eleitorais da Bahia no padrão **001 a 205**, conforme o código anexo.
- Importação complementar da consulta pública do TRE-BA: `https://extranet.tre-ba.jus.br/EndZE/`.
- Importação da planilha ODS de monitoramento.
- Login com perfis de acesso:
  - `admin`
  - `corregedoria_gestor`
  - `corregedoria_analista`
  - `chefe_cartorio`
  - `substituto`
  - `auditor`
- Auto-cadastro com validação por token.
- Recuperação de senha por token.
- Cadastro e manutenção de usuários pelo administrador.
- Dashboard gerencial com indicadores de pendência, atraso, cumprimento, validação e devolução.
- Geração de tarefas por frequência.
- Preenchimento do checklist pelo Chefe/Substituto da Zona.
- Validação/devolução pela Corregedoria.
- Comentários internos e anexos/links de evidência por tarefa.
- Backup completo em JSON e cópia de conferência em Excel.
- Restauração de backup JSON pelo administrador.
- Relatórios PDF e Excel por status, zona e período.
- Auditoria de ações relevantes.

## Como executar localmente

```bash
cd simoc_streamlit_supabase_full
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
streamlit run streamlit_app.py
```

## Configuração no Streamlit Cloud

Em **Settings > Secrets**, configure:

```toml
DATABASE_URL = "postgresql://postgres.xxxxx:SUA-SENHA@aws-0-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
SECRET_KEY = "troque-por-uma-chave-grande"
ADMIN_EMAIL = "admin@tre-ba.jus.br"
ADMIN_PASSWORD = "troque-esta-senha"
APP_BASE_URL = "https://seu-app.streamlit.app"

# Opcional para envio real de validação/recuperação
SMTP_HOST = "smtp.seu-servidor.gov.br"
SMTP_PORT = 587
SMTP_USER = "usuario"
SMTP_PASSWORD = "senha"
EMAIL_REMETENTE = "naoresponda@tre-ba.jus.br"
```

## Primeira carga

Após o primeiro login como administrador:

1. Acesse **Importação**.
2. Clique em **Criar/atualizar schema**.
3. Clique em **Garantir zonas 001-205**.
4. Clique em **Importar consulta pública TRE-BA** para complementar sedes e municípios.
5. Clique em **Importar planilha padrão**.
6. Cadastre os usuários Chefes/Substitutos em **Usuários**.
7. Gere as tarefas em **Gerar tarefas**.

## Observações

- A relação 001-205 garante a base completa de zonas no sistema, mesmo que a consulta pública esteja fora do ar.
- A consulta pública complementa `municipio_sede` e `municipios_abrangidos` quando disponível.
- O backup JSON é o formato adequado para restauração. O Excel é uma cópia para conferência e auditoria administrativa.
- Não envie `.env` nem `.streamlit/secrets.toml` para o GitHub.
