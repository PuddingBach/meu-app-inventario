import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from datetime import datetime

# Verificação EXTRA do SPREADSHEET_ID
SPREADSHEET_ID = st.secrets.get("SPREADSHEET_ID", "")

if not SPREADSHEET_ID or not isinstance(SPREADSHEET_ID, str) or len(SPREADSHEET_ID) < 44:
    st.error(f"""
    ❌ Problema com o SPREADSHEET_ID. Verifique:
    1. Foi adicionado ao secrets.toml?
    2. O ID tem pelo menos 44 caracteres?
    3. O ID atual é: '{SPREADSHEET_ID}'
    """)
    st.stop()

# Adicione isto para debug (remova depois)
st.success(f"✅ ID válido detectado: {SPREADSHEET_ID[:10]}...{SPREADSHEET_ID[-10:]}")

# Verificação EXTRA do SPREADSHEET_ID
SPREADSHEET_ID = st.secrets.get("SPREADSHEET_ID", "")

if not SPREADSHEET_ID or not isinstance(SPREADSHEET_ID, str) or len(SPREADSHEET_ID) < 44:
    st.error(f"""
    ❌ Problema com o SPREADSHEET_ID. Verifique:
    1. Foi adicionado ao secrets.toml?
    2. O ID tem pelo menos 44 caracteres?
    3. O ID atual é: '{SPREADSHEET_ID}'
    """)
    st.stop()

# Adicione isto para debug (remova depois)
st.success(f"✅ ID válido detectado: {SPREADSHEET_ID[:10]}...{SPREADSHEET_ID[-10:]}")

if st.button("🔍 Testar Conexão com Google Sheets"):
    try:
        gc = get_gs_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        st.success(f"✅ Conexão OK! Planilha: '{spreadsheet.title}'")
        st.write("Abas disponíveis:", [ws.title for ws in spreadsheet.worksheets()])
    except Exception as e:
        st.error(f"❌ Falha: {str(e)}")

# aoagar posteriomente
# Configuração inicial
st.set_page_config(page_title="Sistema de Inventário", layout="wide")

# --- VERIFICAÇÃO DAS CREDENCIAIS ---
if 'google_creds' not in st.secrets:
    st.error("❌ Credenciais do Google Sheets não encontradas no secrets.toml")
    st.stop()

try:
    CREDS = service_account.Credentials.from_service_account_info(
        st.secrets["google_creds"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    CLIENT_EMAIL = st.secrets["google_creds"]["client_email"]
except Exception as e:
    st.error(f"❌ Erro ao carregar credenciais: {str(e)}")
    st.stop()

# --- CONFIGURAÇÃO DA PLANILHA ---
SPREADSHEET_ID = st.secrets.get("SPREADSHEET_ID")
if not SPREADSHEET_ID or len(SPREADSHEET_ID) < 44:
    st.error("❌ SPREADSHEET_ID inválido ou não configurado")
    st.stop()

SHEET_NAMES = {
    'movimentacoes': 'movimentacoes',
    'produtos': 'produtos',
    'responsaveis': 'responsaveis',
    'unidades': 'unidades',
    'usuarios': 'usuarios'
}

# --- FUNÇÕES PRINCIPAIS ---
@st.cache_resource(ttl=300)
def get_gs_client():
    """Retorna o cliente autenticado do Google Sheets"""
    try:
        return gspread.authorize(CREDS)
    except Exception as e:
        st.error(f"❌ Falha na autenticação: {str(e)}")
        st.stop()

def load_sheet_data():
    """Carrega todos os dados das planilhas com tratamento robusto de erros"""
    try:
        gc = get_gs_client()
        
        try:
            spreadsheet = gc.open_by_key(SPREADSHEET_ID)
            st.session_state['spreadsheet_title'] = spreadsheet.title
        except gspread.SpreadsheetNotFound:
            st.error(f"📌 Planilha não encontrada. Verifique:")
            st.error(f"1. ID correto: {SPREADSHEET_ID}")
            st.error(f"2. Compartilhada com: {CLIENT_EMAIL}")
            st.error(f"3. Não está na lixeira")
            st.stop()
        
        data = {}
        for key, sheet_name in SHEET_NAMES.items():
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                records = worksheet.get_all_records()
                data[key] = pd.DataFrame(records)
            except gspread.WorksheetNotFound:
                st.warning(f"⚠️ Aba '{sheet_name}' não encontrada - Criando DataFrame vazio")
                data[key] = pd.DataFrame()
            except Exception as e:
                st.error(f"Erro na aba {sheet_name}: {str(e)}")
                data[key] = pd.DataFrame()
        
        return data
    
    except Exception as e:
        st.error(f"🚨 Erro crítico: {str(e)}")
        st.stop()

def save_data(dataframes):
    """Salva dados nas planilhas com verificação em tempo real"""
    try:
        gc = get_gs_client()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        
        for sheet_name, df in dataframes.items():
            if sheet_name not in SHEET_NAMES:
                continue
                
            try:
                worksheet = spreadsheet.worksheet(SHEET_NAMES[sheet_name])
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=SHEET_NAMES[sheet_name], 
                    rows=100, 
                    cols=len(df.columns)
                )  # Fechamento correto dos parênteses aqui
            
            worksheet.clear()
            worksheet.update(
                [df.columns.values.tolist()] + df.fillna('').values.tolist(),
                value_input_option='USER_ENTERED'
            )
        
        st.toast("✅ Dados salvos com sucesso!", icon="✅")
        return True
        
    except Exception as e:
        st.error(f"❌ Falha ao salvar: {str(e)}")
        return False

# --- SISTEMA DE LOGIN ---
def check_login(username, password, users_df):
    """Valida credenciais com tratamento seguro"""
    try:
        if users_df.empty:
            st.warning("Nenhum usuário cadastrado")
            return False
            
        required_cols = ['username', 'senha', 'nivel_acesso']
        if not all(col in users_df.columns for col in required_cols):
            st.error("Estrutura inválida na planilha de usuários")
            return False
            
        user = users_df[
            (users_df['username'].str.strip().str.lower() == username.strip().lower()) &
            (users_df['senha'].astype(str).str.strip() == password.strip())
        ]
        
        if not user.empty:
            st.session_state['user'] = {
                'name': user.iloc[0]['username'],
                'level': user.iloc[0]['nivel_acesso']
            }
            return True
            
        st.warning("Credenciais inválidas")
        return False
        
    except Exception as e:
        st.error(f"Erro no login: {str(e)}")
        return False

# --- INTERFACE ---
def show_login():
    st.title("🔒 Login do Sistema")
    _, _, _, _, users_df = load_sheet_data()
    
    with st.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Entrar"):
            if check_login(username, password, users_df):
                st.rerun()

def main_app():
    st.title(f"📦 Sistema de Inventário - {st.session_state['user']['name']}")
    mov, prod, resp, uni, _ = load_sheet_data()
    
    # Sua lógica de inventário aqui
    st.dataframe(prod)
    
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --- EXECUÇÃO ---
if 'user' not in st.session_state:
    show_login()
else:
    main_app()
# Função para verificar o login
def verificar_login(username, senha, usuarios):
    try:
        # Verificação mais robusta das colunas
        required_columns = ['username', 'senha', 'nivel_acesso']
        missing_columns = [col for col in required_columns if col not in usuarios.columns]
        
        if missing_columns:
            st.error(f"Colunas obrigatórias não encontradas: {', '.join(missing_columns)}")
            return None
        
        # Verificação com tratamento de casos nulos e normalização
        usuario = usuarios.loc[
            (usuarios['username'].str.strip().str.lower() == username.strip().lower()) & 
            (usuarios['senha'].astype(str).str.strip() == senha.strip())
        ]
        
        if not usuario.empty:
            st.session_state['user_authenticated'] = True  # Adiciona estado de autenticação
            st.session_state['user_level'] = usuario.iloc[0]['nivel_acesso']  # Armazena nível de acesso
            return usuario.iloc[0]['nivel_acesso']
        
        st.warning("Credenciais inválidas")  # Feedback mais amigável
        return None
        
    except Exception as e:
        st.error(f"Erro inesperado ao verificar login: {str(e)}")
        return None

# Função para adicionar novo usuário
def adicionar_usuario(usuarios, username, senha, nivel_acesso):
    try:
        # Verificar se o username já está em uso
        if username in usuarios['username'].values:
            st.error(f"Username {username} já está em uso. Escolha outro username.")
            return usuarios
        
        # Criar novo usuário
        novo_usuario = {
            'username': username,
            'senha': senha,
            'nivel_acesso': nivel_acesso
        }
        usuarios = pd.concat([usuarios, pd.DataFrame([novo_usuario])], ignore_index=True)
        st.success("Usuário adicionado com sucesso!")
        return usuarios
    except Exception as e:
        st.error(f"Erro ao adicionar usuário: {e}")
        return usuarios

# Função para editar usuário
def editar_usuario(usuarios, username_antigo, username_novo, senha_nova, nivel_acesso_novo):
    try:
        # Verificar se o username novo já está em uso
        if username_novo != username_antigo and username_novo in usuarios['username'].values:
            st.error(f"Username {username_novo} já está em uso. Escolha outro username.")
            return usuarios
        
        # Atualizar os dados do usuário
        usuarios.loc[usuarios['username'] == username_antigo, 'username'] = username_novo
        usuarios.loc[usuarios['username'] == username_novo, 'senha'] = senha_nova
        usuarios.loc[usuarios['username'] == username_novo, 'nivel_acesso'] = nivel_acesso_novo
        st.success("Usuário atualizado com sucesso!")
        return usuarios
    except Exception as e:
        st.error(f"Erro ao editar usuário: {e}")
        return usuarios

# Função para adicionar produto
def adicionar_produto(produtos, nome_produto, id_produto, quantidade_estoque, unidade_medida, categoria):
    try:
        novo_produto = {
            'ID Produto': id_produto,
            'Nome do Produto': nome_produto,
            'Quantidade em Estoque': quantidade_estoque,
            'Unidade de Medida': unidade_medida,
            'Categoria': categoria
        }
        produtos = pd.concat([produtos, pd.DataFrame([novo_produto])], ignore_index=True)
        return produtos
    except Exception as e:
        st.error(f"Erro ao adicionar produto: {e}")
        return produtos

# Função para editar produto
def editar_produto(produtos, id_produto, nome_produto, quantidade_estoque, unidade_medida, categoria):
    try:
        produtos.loc[produtos['ID Produto'] == id_produto, 'Nome do Produto'] = nome_produto
        produtos.loc[produtos['ID Produto'] == id_produto, 'Quantidade em Estoque'] = quantidade_estoque
        produtos.loc[produtos['ID Produto'] == id_produto, 'Unidade de Medida'] = unidade_medida
        produtos.loc[produtos['ID Produto'] == id_produto, 'Categoria'] = categoria
        return produtos
    except Exception as e:
        st.error(f"Erro ao editar produto: {e}")
        return produtos

# Função para excluir produto
def excluir_produto(produtos, id_produto):
    try:
        produtos = produtos[produtos['ID Produto'] != id_produto]
        return produtos
    except Exception as e:
        st.error(f"Erro ao excluir produto: {e}")
        return produtos

# Função para o menu de navegação
def menu():
    if st.button("..."):
        st.session_state['menu_aberto'] = not st.session_state.get('menu_aberto', False)
    
    if st.session_state.get('menu_aberto', False):
        if st.session_state['nivel_acesso'] in ["Gerente", "Operador"]:
            if st.button("Movimentar"):
                st.session_state['pagina'] = 'movimentacao'
                st.session_state['menu_aberto'] = False
        if st.session_state['nivel_acesso'] == "Gerente":
            if st.button("Editar"):
                st.session_state['pagina'] = 'editar'
                st.session_state['menu_aberto'] = False
            if st.button("Usuários"):
                st.session_state['pagina'] = 'usuarios'
                st.session_state['menu_aberto'] = False
        if st.session_state['nivel_acesso'] in ["Gerente", "Operador"]:
            if st.button("Histórico"):
                st.session_state['pagina'] = 'historico'
                st.session_state['menu_aberto'] = False
        if st.session_state['nivel_acesso'] == "Gerente":
            if st.button("Responsáveis/Unidades"):
                st.session_state['pagina'] = 'responsaveis_unidades'
                st.session_state['menu_aberto'] = False
        if st.button("Sair"):
            st.session_state['logado'] = False
            st.session_state['username'] = None
            st.session_state['nivel_acesso'] = None
            st.session_state['pagina'] = 'principal'
            st.rerun()

# Página de Login
def tela_login(usuarios):
    st.title("Login")
    username = st.text_input("Username")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar"):
        nivel_acesso = verificar_login(username, senha, usuarios)
        if nivel_acesso:
            st.session_state['logado'] = True
            st.session_state['username'] = username
            st.session_state['nivel_acesso'] = nivel_acesso
            st.session_state['pagina'] = 'principal'
            st.rerun()
        else:
            st.error("Usuário ou senha incorretos.")

# Página de Usuários
def pagina_usuarios(usuarios):
    st.title("Usuários")
    menu()  # Adicionar o menu aqui
    
    # Exibir lista de usuários (ocultando a senha)
    st.markdown("### Lista de Usuários")
    st.dataframe(
        usuarios[['username', 'nivel_acesso']],  # Não exibir a coluna 'senha'
        use_container_width=True,
        hide_index=True,
        column_config={
            "username": "Username",
            "nivel_acesso": "Nível de Acesso"
        }
    )
    
    # Formulário para adicionar novo usuário
    with st.form("form_adicionar_usuario"):
        st.markdown("### Adicionar Novo Usuário")
        username = st.text_input("Username")
        senha = st.text_input("Senha", type="password")
        nivel_acesso = st.selectbox("Nível de Acesso", ["Gerente", "Operador", "Visualizador"])
        if st.form_submit_button("Adicionar Usuário"):
            usuarios = adicionar_usuario(usuarios, username, senha, nivel_acesso)
            salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], st.session_state['responsaveis'], st.session_state['unidades'], usuarios)
            st.session_state['usuarios'] = usuarios
            time.sleep(1)  # Delay de 1 segundo
            st.cache_data.clear()  # Limpar o cache
            st.rerun()  # Recarregar a página
    
    # Formulário para editar usuário
    with st.form("form_editar_usuario"):
        st.markdown("### Editar Usuário")
        username_antigo = st.selectbox("Selecione o usuário para editar", usuarios['username'].unique())
        username_novo = st.text_input("Novo Username")
        senha_nova = st.text_input("Nova Senha", type="password")
        nivel_acesso_novo = st.selectbox("Novo Nível de Acesso", ["Gerente", "Operador", "Visualizador"])
        if st.form_submit_button("Editar Usuário"):
            usuarios = editar_usuario(usuarios, username_antigo, username_novo, senha_nova, nivel_acesso_novo)
            salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], st.session_state['responsaveis'], st.session_state['unidades'], usuarios)
            st.session_state['usuarios'] = usuarios
            time.sleep(1)  # Delay de 1 segundo
            st.cache_data.clear()  # Limpar o cache
            st.rerun()  # Recarregar a página
    
    # Botão para voltar à página principal
    if st.button("Voltar à Página Principal"):
        st.session_state['pagina'] = 'principal'

# Página Principal
def pagina_principal(produtos, movimentacoes, responsaveis, unidades):
    st.title("Inventário de Produtos")
    menu()  # Adicionar o menu aqui
    
    # Campo de pesquisa
    pesquisa = st.text_input("Pesquisar Produto", "")
    
    # Filtros de ordenação
    ordenar_por = st.selectbox("Ordenar por", ["Nome (A-Z)", "Nome (Z-A)", "Quantidade (Menor para Maior)", "Quantidade (Maior para Menor)"])
    
    # Aplicar ordenação
    if ordenar_por == "Nome (A-Z)":
        produtos = produtos.sort_values(by="Nome do Produto", ascending=True)
    elif ordenar_por == "Nome (Z-A)":
        produtos = produtos.sort_values(by="Nome do Produto", ascending=False)
    elif ordenar_por == "Quantidade (Menor para Maior)":
        produtos = produtos.sort_values(by="Quantidade em Estoque", ascending=True)
    elif ordenar_por == "Quantidade (Maior para Menor)":
        produtos = produtos.sort_values(by="Quantidade em Estoque", ascending=False)
    
    # Filtrar por pesquisa
    if pesquisa:
        produtos = produtos[produtos['Nome do Produto'].str.contains(pesquisa, case=False)]
    
    # Exibir lista de produtos de forma fluida e sem bordas
    st.markdown("### Lista de Produtos")
    st.dataframe(
        produtos,
        use_container_width=True,  # Ajusta a largura ao contêiner
        hide_index=True,  # Remove o índice
        column_config={
            "ID Produto": "ID Produto",  # Mostra o ID do Produto
            "Nome do Produto": "Produto",
            "Quantidade em Estoque": "Estoque",
            "Unidade de Medida": "Unidade",
            "Categoria": "Categoria"
        }
    )

# Página de Movimentação
def pagina_movimentacao(movimentacoes, produtos, responsaveis, unidades):
    st.title("Nova Movimentação")
    menu()  # Adicionar o menu aqui
    
    # Formulário para inserir movimentação
    with st.form("form_movimentacao"):
        # Selecionar produto
        produto_nome = st.selectbox("Produto", produtos['Nome do Produto'].unique())
        
        # Selecionar responsável
        responsavel_nome = st.selectbox("Responsável", responsaveis['Nome do Responsável'].unique())
        
        # Selecionar unidade
        unidade_nome = st.selectbox("Unidade", unidades['Nome da Unidade'].unique())
        
        # Tipo de operação
        tipo = st.selectbox("Tipo de Operação", ["Entrada", "Saída"])
        
        # Quantidade
        quantidade = st.number_input("Quantidade", min_value=1)
        
        # Fornecedor
        fornecedor = st.text_input("Fornecedor")
        
        # Razão da movimentação
        razao = st.text_input("Razão da Movimentação")
        
        # Data
        data = st.date_input("Data")
        
        # Botão para salvar
        if st.form_submit_button("Salvar Movimentação"):
            movimentacoes, produtos = adicionar_movimentacao(movimentacoes, produtos, responsaveis, unidades, produto_nome, responsavel_nome, unidade_nome, tipo, quantidade, fornecedor, razao, data)
            salvar_planilhas(movimentacoes, produtos, responsaveis, unidades, st.session_state['usuarios'])
            
            # Recarregar as planilhas após salvar
            movimentacoes, produtos, responsaveis, unidades, usuarios = carregar_planilhas()
            
            # Atualizar o estado da aplicação
            st.session_state['movimentacoes'] = movimentacoes
            st.session_state['produtos'] = produtos
            st.session_state['responsaveis'] = responsaveis
            st.session_state['unidades'] = unidades
            st.session_state['usuarios'] = usuarios
            
            st.success("Movimentação salva com sucesso!")
            
                       # Limpar o cache antes de recarregar a página
            time.sleep(1)  # Delay de 1 segundo
            st.cache_data.clear()
            st.session_state['pagina'] = 'principal'  # Redirecionar para a tela inicial
            st.rerun()  # Forçar atualização da página
    
    # Botão para voltar à página principal
    if st.button("Voltar à Página Principal"):
        st.session_state['pagina'] = 'principal'

# Página para Editar
import pandas as pd
import streamlit as st
import time

def gerar_novo_id(produtos):
    """Gera um novo ID automaticamente baseado no maior ID existente + 1, evitando conflitos"""
    if produtos.empty:
        return 1
    
    # Garante que estamos trabalhando com números inteiros
    ids_existentes = pd.to_numeric(produtos['ID Produto'], errors='coerce').dropna()
    
    if ids_existentes.empty:
        return 1
    
    max_id = int(ids_existentes.max())
    
    # Verifica se há algum número faltante na sequência
    todos_ids = set(range(1, max_id + 1))
    ids_atuais = set(ids_existentes.astype(int))
    ids_disponiveis = todos_ids - ids_atuais
    
    if ids_disponiveis:
        return min(ids_disponiveis)
    return max_id + 1

def pagina_editar(movimentacoes, produtos, responsaveis, unidades):
    st.title("Editar Cadastro de Produtos")
    menu()  # Adicionar o menu aqui

    # Selecionar a ação (Adicionar, Editar, Excluir)
    acao = st.radio("Selecione a ação:", ["Adicionar", "Editar", "Excluir"], horizontal=True)

    if acao == "Adicionar":
        with st.form("form_adicionar", clear_on_submit=True):
            st.markdown("### Adicionar Novo Produto")
            
            # Gerar novo ID automaticamente (garantindo que não haja conflitos)
            novo_id = gerar_novo_id(produtos)
            st.write(f"**ID do Produto atribuído automaticamente:** {novo_id}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nome_produto = st.text_input("Nome do Produto*", 
                                          help="Nome descritivo do produto")
                quantidade_estoque = st.number_input("Quantidade em Estoque*", min_value=0, 
                                                  help="Quantidade atual em estoque")
            
            with col2:
                # Verifica se a coluna 'Unidade' existe no DataFrame unidades
                if 'Unidade' in unidades.columns:
                    unidade_opcoes = unidades['Unidade'].unique()
                else:
                    unidade_opcoes = ["un", "kg", "g", "l", "ml"]  # Valores padrão
                    st.warning("Unidades de medida não encontradas. Usando valores padrão.")
                
                unidade_medida = st.selectbox("Unidade de Medida*", unidade_opcoes, 
                                            help="Unidade de medida do produto")
                categoria = st.text_input("Categoria", 
                                       help="Categoria do produto (opcional)")
            
            st.markdown("*Campos obrigatórios")
            
            # Botão de submit explícito
            submitted = st.form_submit_button("Adicionar Produto")
            if submitted:
                if nome_produto.strip() == "":
                    st.error("Erro: O nome do produto é obrigatório.")
                else:
                    # Verificar se o nome do produto já existe
                    if nome_produto in produtos['Nome do Produto'].values:
                        st.error("Erro: Já existe um produto com este nome.")
                    else:
                        # Adicionar o novo produto
                        novo_produto = {
                            'ID Produto': novo_id,
                            'Nome do Produto': nome_produto,
                            'Quantidade em Estoque': quantidade_estoque,
                            'Unidade de Medida': unidade_medida,
                            'Categoria': categoria
                        }
                        
                        produtos = pd.concat([produtos, pd.DataFrame([novo_produto])], ignore_index=True)
                        salvar_planilhas(movimentacoes, produtos, responsaveis, unidades, st.session_state['usuarios'])
                        
                        st.success("Produto adicionado com sucesso!")
                        time.sleep(1.5)
                        st.cache_data.clear()
                        st.rerun()

    elif acao == "Editar":
        with st.form("form_editar", clear_on_submit=True):
            st.markdown("### Editar Produto Existente")
            
            # Selecionar o produto a ser editado
            produto_selecionado = st.selectbox("Selecione o produto para editar*", 
                                            produtos['Nome do Produto'].unique(),
                                            help="Selecione o produto que deseja editar")
            
            # Obter os dados atuais do produto selecionado
            produto_info = produtos[produtos['Nome do Produto'] == produto_selecionado].iloc[0]
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Mostrar ID (não editável)
                st.text_input("ID do Produto (não editável)", value=produto_info['ID Produto'], disabled=True)
                
                # Campos editáveis
                novo_nome = st.text_input("Nome do Produto*", value=produto_info['Nome do Produto'],
                                       help="Novo nome para o produto")
                nova_quantidade = st.number_input("Quantidade em Estoque*", 
                                               value=int(produto_info['Quantidade em Estoque']),
                                               min_value=0,
                                               help="Nova quantidade em estoque")
            
            with col2:
                # Verifica se a coluna 'Unidade' existe no DataFrame unidades
                if 'Unidade' in unidades.columns:
                    unidade_opcoes = unidades['Unidade'].unique()
                    try:
                        unidade_index = list(unidade_opcoes).index(produto_info['Unidade de Medida'])
                    except ValueError:
                        unidade_index = 0
                else:
                    unidade_opcoes = ["un", "kg", "g", "l", "ml"]
                    unidade_index = 0
                    st.warning("Unidades de medida não encontradas. Usando valores padrão.")
                
                nova_unidade = st.selectbox("Unidade de Medida*", 
                                         unidade_opcoes,
                                         index=unidade_index,
                                         help="Nova unidade de medida")
                nova_categoria = st.text_input("Categoria", 
                                            value=produto_info['Categoria'],
                                            help="Nova categoria (opcional)")
            
            st.markdown("*Campos obrigatórios")
            
            # Botão de submit explícito
            submitted = st.form_submit_button("Salvar Alterações")
            if submitted:
                if novo_nome.strip() == "":
                    st.error("Erro: O nome do produto é obrigatório.")
                else:
                    # Verificar se o novo nome já existe (exceto para o próprio produto)
                    if (novo_nome != produto_selecionado and 
                        novo_nome in produtos['Nome do Produto'].values):
                        st.error("Erro: Já existe outro produto com este nome.")
                    else:
                        # Atualizar os dados do produto
                        produtos.loc[produtos['ID Produto'] == produto_info['ID Produto'], 'Nome do Produto'] = novo_nome
                        produtos.loc[produtos['ID Produto'] == produto_info['ID Produto'], 'Quantidade em Estoque'] = nova_quantidade
                        produtos.loc[produtos['ID Produto'] == produto_info['ID Produto'], 'Unidade de Medida'] = nova_unidade
                        produtos.loc[produtos['ID Produto'] == produto_info['ID Produto'], 'Categoria'] = nova_categoria
                        
                        salvar_planilhas(movimentacoes, produtos, responsaveis, unidades, st.session_state['usuarios'])
                        
                        st.success("Produto atualizado com sucesso!")
                        time.sleep(1.5)
                        st.cache_data.clear()
                        st.rerun()

    elif acao == "Excluir":
        with st.form("form_excluir", clear_on_submit=True):
            st.markdown("### Excluir Produto")
            
            # Selecionar o produto a ser excluído
            produto_selecionado = st.selectbox("Selecione o produto para excluir*", 
                                             produtos['Nome do Produto'].unique(),
                                             help="Selecione o produto que deseja excluir")
            
            # Obter informações do produto
            produto_info = produtos[produtos['Nome do Produto'] == produto_selecionado].iloc[0]
            id_produto = produto_info['ID Produto']
            
            # Verificar se há movimentações associadas
            movimentacoes_produto = movimentacoes[movimentacoes['ID Produto'] == id_produto]
            tem_movimentacoes = not movimentacoes_produto.empty
            
            # Exibir informações do produto
            st.warning("Você está prestes a excluir o seguinte produto:")
            st.write(f"**ID:** {id_produto}")
            st.write(f"**Nome:** {produto_info['Nome do Produto']}")
            st.write(f"**Estoque atual:** {produto_info['Quantidade em Estoque']} {produto_info['Unidade de Medida']}")
            
            if tem_movimentacoes:
                st.warning(f"⚠️ ATENÇÃO: Este produto possui {len(movimentacoes_produto)} movimentação(ões) registrada(s).")
                
                # Opção simplificada - sempre manter as movimentações com ID substituído
                st.info("As movimentações deste produto serão mantidas, mas o ID do produto será marcado como 'DESCONHECIDO'.")
            
            confirmacao = st.checkbox("Confirmo que desejo excluir este produto permanentemente", key="confirmacao_exclusao")
            
            submitted = st.form_submit_button("Confirmar Exclusão")
            
            if submitted and confirmacao:
                try:
                    # Excluir o produto
                    produtos = produtos[produtos['ID Produto'] != id_produto]
                    
                    # Tratar movimentações - sempre substituir por 'DESCONHECIDO'
                    if tem_movimentacoes:
                        movimentacoes.loc[movimentacoes['ID Produto'] == id_produto, 'ID Produto'] = 'DESCONHECIDO'
                        movimentacoes.loc[movimentacoes['ID Produto'] == id_produto, 'Nome do Produto'] = 'PRODUTO DESCONHECIDO'
                    
                    salvar_planilhas(movimentacoes, produtos, responsaveis, unidades, st.session_state['usuarios'])
                    
                    st.success("Produto excluído com sucesso!")
                    if tem_movimentacoes:
                        st.info("As movimentações foram mantidas com o produto marcado como 'DESCONHECIDO'.")
                    
                    time.sleep(1.5)
                    st.cache_data.clear()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Erro ao excluir produto: {str(e)}")
            elif submitted and not confirmacao:
                st.error("Por favor, marque a caixa de confirmação para excluir o produto.")

    # Botão para voltar à página principal (única instância)
    if st.button("⏎ Voltar à Página Principal"):
        st.session_state['pagina'] = 'principal'
# Página de Histórico
def pagina_historico(movimentacoes, produtos, responsaveis, unidades):
    st.title("Histórico de Movimentações")
    menu()  # Adicionar o menu aqui
    
    # Verificar se as colunas necessárias existem
    if 'ID Responsavel' not in responsaveis.columns:
        st.error("A coluna 'ID Responsavel' não foi encontrada na planilha 'responsaveis'.")
        return
    
    # Mesclar dados para exibir nomes em vez de IDs
    historico_completo = movimentacoes.merge(
        produtos[['ID Produto', 'Nome do Produto']],
        on='ID Produto',
        how='left'
    ).merge(
        responsaveis[['ID Responsavel', 'Nome do Responsável']],
        on='ID Responsavel',
        how='left'
    ).merge(
        unidades[['ID Unidade', 'Nome da Unidade']],
        on='ID Unidade',
        how='left'
    )
    
    # Verificar se as colunas esperadas existem após o merge
    colunas_esperadas = ['Nome do Produto', 'Nome do Responsável', 'Nome da Unidade', 'Tipo', 'Quantidade', 'Fornecedor', 'Razão', 'Data']
    colunas_disponiveis = historico_completo.columns.tolist()
    
    # Apenas incluir colunas que existem no DataFrame
    colunas_para_exibir = [col for col in colunas_esperadas if col in colunas_disponiveis]
    
    # Converter coluna de Data para datetime se não estiver no formato correto
    if not pd.api.types.is_datetime64_any_dtype(historico_completo['Data']):
        historico_completo['Data'] = pd.to_datetime(historico_completo['Data'], errors='coerce')
    
    # Filtros
    st.subheader("Filtros")
    
    # Filtro por Unidade - Corrigindo o erro de tipos mistos
    unidades_disponiveis = ['Todas'] + sorted(
        historico_completo['Nome da Unidade'].astype(str).unique().tolist(),
        key=lambda x: x.lower()  # Ordena case-insensitive
    )
    
    unidade_selecionada = st.selectbox(
        "Selecione a Unidade:",
        unidades_disponiveis,
        index=0
    )
    
    # Filtro por Período
    col1, col2 = st.columns(2)
    with col1:
        data_inicio = st.date_input(
            "Data de início:",
            value=historico_completo['Data'].min().date(),
            min_value=historico_completo['Data'].min().date(),
            max_value=historico_completo['Data'].max().date()
        )
    with col2:
        data_fim = st.date_input(
            "Data de fim:",
            value=historico_completo['Data'].max().date(),
            min_value=historico_completo['Data'].min().date(),
            max_value=historico_completo['Data'].max().date()
        )
    
    # Aplicar filtros
    historico_filtrado = historico_completo.copy()
    
    # Filtrar por unidade
    if unidade_selecionada != 'Todas':
        historico_filtrado = historico_filtrado[
            historico_filtrado['Nome da Unidade'].astype(str) == unidade_selecionada
        ]
    
    # Filtrar por período
    historico_filtrado = historico_filtrado[
        (historico_filtrado['Data'].dt.date >= data_inicio) & 
        (historico_filtrado['Data'].dt.date <= data_fim)
    ]
    
    # Exibir o histórico de movimentações filtrado
    st.dataframe(
        historico_filtrado[colunas_para_exibir],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Nome do Produto": "Produto",
            "Nome do Responsável": "Responsável",
            "Nome da Unidade": "Unidade",
            "Tipo": "Tipo",
            "Quantidade": "Quantidade",
            "Fornecedor": "Fornecedor",
            "Razão": "Razão",
            "Data": "Data"
        }
    )
    
    # Botão para voltar à página principal
    if st.button("Voltar à Página Principal"):
        st.session_state['pagina'] = 'principal'

        
def pagina_responsaveis_unidades(responsaveis, unidades):
    st.title("📋 Responsáveis e Unidades")
    menu()  # Adicionar o menu aqui

    # Função para gerar o próximo ID disponível
    def proximo_id(df, coluna_id):
        if df.empty:
            return 1
        else:
            return df[coluna_id].max() + 1

    # Função para adicionar responsável
    def adicionar_responsavel(responsaveis, nome_responsavel, id_unidade, cargo, telefone):
        novo_id = proximo_id(responsaveis, 'ID Responsavel')
        novo_responsavel = {
            'ID Responsavel': novo_id,
            'Nome do Responsável': nome_responsavel,
            'ID Unidade': id_unidade,
            'Cargo': cargo,
            'Telefone': telefone
        }
        return pd.concat([responsaveis, pd.DataFrame([novo_responsavel])], ignore_index=True)

    # Função para editar responsável
    def editar_responsavel(responsaveis, nome_antigo, nome_novo, id_unidade, cargo, telefone):
        mask = responsaveis['Nome do Responsável'] == nome_antigo
        responsaveis.loc[mask, 'Nome do Responsável'] = nome_novo
        responsaveis.loc[mask, 'ID Unidade'] = id_unidade
        responsaveis.loc[mask, 'Cargo'] = cargo
        responsaveis.loc[mask, 'Telefone'] = telefone
        return responsaveis

    # Função para excluir responsável
    def excluir_responsavel(responsaveis, nome_responsavel):
        return responsaveis[responsaveis['Nome do Responsável'] != nome_responsavel]

    # Função para adicionar unidade
    def adicionar_unidade(unidades, nome_unidade, endereco, cidade, estado):
        novo_id = proximo_id(unidades, 'ID Unidade')
        nova_unidade = {
            'ID Unidade': novo_id,
            'Nome da Unidade': nome_unidade,
            'Endereço': endereco,
            'Cidade': cidade,
            'Estado': estado
        }
        return pd.concat([unidades, pd.DataFrame([nova_unidade])], ignore_index=True)

    # Função para editar unidade
    def editar_unidade(unidades, nome_antigo, nome_novo, endereco, cidade, estado):
        mask = unidades['Nome da Unidade'] == nome_antigo
        unidades.loc[mask, 'Nome da Unidade'] = nome_novo
        unidades.loc[mask, 'Endereço'] = endereco
        unidades.loc[mask, 'Cidade'] = cidade
        unidades.loc[mask, 'Estado'] = estado
        return unidades

    # Função para excluir unidade
    def excluir_unidade(unidades, nome_unidade):
        return unidades[unidades['Nome da Unidade'] != nome_unidade]

    # --- SEÇÃO DE RESPONSÁVEIS ---
    st.markdown("## 👥 Responsáveis")
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Adicionar Responsável", key="btn_add_resp_rpu"):
            st.session_state['mostrar_adicionar_responsavel'] = True
            st.session_state['mostrar_editar_responsavel'] = False
            st.session_state['mostrar_excluir_responsavel'] = False
    with col2:
        if st.button("✏️ Editar Responsável", key="btn_edit_resp_rpu"):
            st.session_state['mostrar_adicionar_responsavel'] = False
            st.session_state['mostrar_editar_responsavel'] = True
            st.session_state['mostrar_excluir_responsavel'] = False
    with col3:
        if st.button("🗑️ Excluir Responsável", key="btn_del_resp_rpu"):
            st.session_state['mostrar_adicionar_responsavel'] = False
            st.session_state['mostrar_editar_responsavel'] = False
            st.session_state['mostrar_excluir_responsavel'] = True

    # Formulário de adição
    if st.session_state.get('mostrar_adicionar_responsavel', False):
        with st.form("form_add_resp_rpu"):
            st.markdown("### Adicionar Novo Responsável")
            nome = st.text_input("Nome Completo", key="nome_resp_add_rpu")
            id_unidade = st.number_input("ID Unidade", min_value=1, key="id_unid_resp_add_rpu")
            cargo = st.text_input("Cargo", key="cargo_resp_add_rpu")
            telefone = st.text_input("Telefone", key="tel_resp_add_rpu")
            
            if st.form_submit_button("💾 Salvar Responsável"):
                try:
                    responsaveis = adicionar_responsavel(responsaveis, nome, id_unidade, cargo, telefone)
                    st.session_state['responsaveis'] = responsaveis
                    salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], 
                                    responsaveis, st.session_state['unidades'], st.session_state['usuarios'])
                    st.success("✅ Responsável adicionado com sucesso!")
                    st.session_state['mostrar_adicionar_responsavel'] = False
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

    # Formulário de edição
    if st.session_state.get('mostrar_editar_responsavel', False):
        with st.form("form_edit_resp_rpu"):
            st.markdown("### Editar Responsável")
            nome_antigo = st.selectbox("Selecione o responsável", responsaveis['Nome do Responsável'].unique(), 
                                      key="select_edit_resp_rpu")
            novo_nome = st.text_input("Novo Nome", key="novo_nome_resp_rpu")
            id_unidade = st.number_input("ID Unidade", min_value=1, key="id_unid_edit_resp_rpu")
            cargo = st.text_input("Cargo", key="cargo_edit_resp_rpu")
            telefone = st.text_input("Telefone", key="tel_edit_resp_rpu")
            
            if st.form_submit_button("💾 Salvar Alterações"):
                try:
                    responsaveis = editar_responsavel(responsaveis, nome_antigo, novo_nome, id_unidade, cargo, telefone)
                    st.session_state['responsaveis'] = responsaveis
                    salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], 
                                    responsaveis, st.session_state['unidades'], st.session_state['usuarios'])
                    st.success("✅ Responsável atualizado com sucesso!")
                    st.session_state['mostrar_editar_responsavel'] = False
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

    # Formulário de exclusão
    if st.session_state.get('mostrar_excluir_responsavel', False):
        with st.form("form_del_resp_rpu"):
            st.markdown("### Excluir Responsável")
            nome = st.selectbox("Selecione o responsável", responsaveis['Nome do Responsável'].unique(), 
                              key="select_del_resp_rpu")
            
            if st.form_submit_button("❌ Confirmar Exclusão"):
                try:
                    responsaveis = excluir_responsavel(responsaveis, nome)
                    st.session_state['responsaveis'] = responsaveis
                    salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], 
                                    responsaveis, st.session_state['unidades'], st.session_state['usuarios'])
                    st.success("✅ Responsável removido com sucesso!")
                    st.session_state['mostrar_excluir_responsavel'] = False
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

    # Tabela de responsáveis
    st.dataframe(
        responsaveis,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID Responsavel": st.column_config.NumberColumn("ID"),
            "Nome do Responsável": "Responsável",
            "ID Unidade": st.column_config.NumberColumn("Unidade"),
            "Cargo": "Cargo",
            "Telefone": "Telefone"
        }
    )

    # --- SEÇÃO DE UNIDADES ---
    st.markdown("## 🏢 Unidades")
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Adicionar Unidade", key="btn_add_unid_rpu"):
            st.session_state['mostrar_adicionar_unidade'] = True
            st.session_state['mostrar_editar_unidade'] = False
            st.session_state['mostrar_excluir_unidade'] = False
    with col2:
        if st.button("✏️ Editar Unidade", key="btn_edit_unid_rpu"):
            st.session_state['mostrar_adicionar_unidade'] = False
            st.session_state['mostrar_editar_unidade'] = True
            st.session_state['mostrar_excluir_unidade'] = False
    with col3:
        if st.button("🗑️ Excluir Unidade", key="btn_del_unid_rpu"):
            st.session_state['mostrar_adicionar_unidade'] = False
            st.session_state['mostrar_editar_unidade'] = False
            st.session_state['mostrar_excluir_unidade'] = True

    # Formulário de adição
    if st.session_state.get('mostrar_adicionar_unidade', False):
        with st.form("form_add_unid_rpu"):
            st.markdown("### Adicionar Nova Unidade")
            nome = st.text_input("Nome da Unidade", key="nome_unid_add_rpu")
            endereco = st.text_input("Endereço", key="end_unid_add_rpu")
            cidade = st.text_input("Cidade", key="cid_unid_add_rpu")
            estado = st.text_input("Estado", key="est_unid_add_rpu")
            
            if st.form_submit_button("💾 Salvar Unidade"):
                try:
                    unidades = adicionar_unidade(unidades, nome, endereco, cidade, estado)
                    st.session_state['unidades'] = unidades
                    salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], 
                                   st.session_state['responsaveis'], unidades, st.session_state['usuarios'])
                    st.success("✅ Unidade adicionada com sucesso!")
                    st.session_state['mostrar_adicionar_unidade'] = False
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

    # Formulário de edição
    if st.session_state.get('mostrar_editar_unidade', False):
        with st.form("form_edit_unid_rpu"):
            st.markdown("### Editar Unidade")
            nome_antigo = st.selectbox("Selecione a unidade", unidades['Nome da Unidade'].unique(), 
                                     key="select_edit_unid_rpu")
            novo_nome = st.text_input("Novo Nome", key="novo_nome_unid_rpu")
            endereco = st.text_input("Endereço", key="end_edit_unid_rpu")
            cidade = st.text_input("Cidade", key="cid_edit_unid_rpu")
            estado = st.text_input("Estado", key="est_edit_unid_rpu")
            
            if st.form_submit_button("💾 Salvar Alterações"):
                try:
                    unidades = editar_unidade(unidades, nome_antigo, novo_nome, endereco, cidade, estado)
                    st.session_state['unidades'] = unidades
                    salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], 
                                   st.session_state['responsaveis'], unidades, st.session_state['usuarios'])
                    st.success("✅ Unidade atualizada com sucesso!")
                    st.session_state['mostrar_editar_unidade'] = False
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

    # Formulário de exclusão
    if st.session_state.get('mostrar_excluir_unidade', False):
        with st.form("form_del_unid_rpu"):
            st.markdown("### Excluir Unidade")
            nome = st.selectbox("Selecione a unidade", unidades['Nome da Unidade'].unique(), 
                              key="select_del_unid_rpu")
            
            if st.form_submit_button("❌ Confirmar Exclusão"):
                try:
                    unidades = excluir_unidade(unidades, nome)
                    st.session_state['unidades'] = unidades
                    salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], 
                                   st.session_state['responsaveis'], unidades, st.session_state['usuarios'])
                    st.success("✅ Unidade removida com sucesso!")
                    st.session_state['mostrar_excluir_unidade'] = False
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Erro: {str(e)}")

    # Tabela de unidades
    st.dataframe(
        unidades,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID Unidade": st.column_config.NumberColumn("ID"),
            "Nome da Unidade": "Unidade",
            "Endereço": "Endereço",
            "Cidade": "Cidade",
            "Estado": "Estado"
        }
    )

    # Botão de voltar
    if st.button("← Voltar à Página Principal", key="btn_voltar_principal_rpu"):
        st.session_state['pagina'] = 'principal'
# Função principal
def main():
    # Carregar planilhas
    movimentacoes, produtos, responsaveis, unidades, usuarios = carregar_planilhas()
    
    # Inicializar estado da página
    if 'pagina' not in st.session_state:
        st.session_state['pagina'] = 'principal'
    
    # Inicializar estado de login
    if 'logado' not in st.session_state:
        st.session_state['logado'] = False
    
    # Inicializar estado de usuário
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'nivel_acesso' not in st.session_state:
        st.session_state['nivel_acesso'] = None
    
    # Inicializar estado das planilhas
    if 'movimentacoes' not in st.session_state:
        st.session_state['movimentacoes'] = movimentacoes
    if 'produtos' not in st.session_state:
        st.session_state['produtos'] = produtos
    if 'responsaveis' not in st.session_state:
        st.session_state['responsaveis'] = responsaveis
    if 'unidades' not in st.session_state:
        st.session_state['unidades'] = unidades
    if 'usuarios' not in st.session_state:
        st.session_state['usuarios'] = usuarios
    
    # Verificar se o usuário está logado
    if not st.session_state['logado']:
        tela_login(usuarios)
    else:
        # Navegação entre páginas
        if st.session_state['pagina'] == 'principal':
            pagina_principal(produtos, movimentacoes, responsaveis, unidades)
        elif st.session_state['pagina'] == 'movimentacao':
            pagina_movimentacao(movimentacoes, produtos, responsaveis, unidades)
        elif st.session_state['pagina'] == 'editar':
            pagina_editar(movimentacoes, produtos, responsaveis, unidades)
        elif st.session_state['pagina'] == 'responsaveis_unidades':
            pagina_responsaveis_unidades(responsaveis, unidades)
        elif st.session_state['pagina'] == 'historico':
            pagina_historico(movimentacoes, produtos, responsaveis, unidades)
        elif st.session_state['pagina'] == 'usuarios':
            pagina_usuarios(usuarios)

# Função para salvar as planilhas
def salvar_planilhas(movimentacoes, produtos, responsaveis, unidades, usuarios):
    try:
        with pd.ExcelWriter('inventario.xlsx', engine='openpyxl') as writer:
            movimentacoes.to_excel(writer, sheet_name='movimentacoes', index=False)
            produtos.to_excel(writer, sheet_name='produtos', index=False)
            responsaveis.to_excel(writer, sheet_name='responsaveis', index=False)
            unidades.to_excel(writer, sheet_name='unidades', index=False)
            usuarios.to_excel(writer, sheet_name='usuarios', index=False)
        st.success("Dados salvos com sucesso!")
    except Exception as e:
        st.error(f"Erro ao salvar planilhas: {e}")
# Executar o aplicativo
if __name__ == "__main__":
    main()
