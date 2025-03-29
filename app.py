import streamlit as st
import pandas as pd
import time  # Para adicionar delay

# Função para carregar as planilhas
@st.cache_data
def carregar_planilhas():
    try:
        movimentacoes = pd.read_excel('inventario.xlsx', sheet_name='movimentacoes')
        produtos = pd.read_excel('inventario.xlsx', sheet_name='produtos')
        responsaveis = pd.read_excel('inventario.xlsx', sheet_name='responsaveis')
        unidades = pd.read_excel('inventario.xlsx', sheet_name='unidades')
        usuarios = pd.read_excel('inventario.xlsx', sheet_name='usuarios')
        
        # Verificar se as colunas necessárias existem
        colunas_necessarias = ['username', 'senha', 'nivel_acesso']
        if not all(coluna in usuarios.columns for coluna in colunas_necessarias):
            st.error(f"As colunas necessárias {colunas_necessarias} não foram encontradas na planilha 'usuarios'.")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        return movimentacoes, produtos, responsaveis, unidades, usuarios
    except Exception as e:
        st.error(f"Erro ao carregar planilhas: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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

# Função para adicionar movimentação
def adicionar_movimentacao(movimentacoes, produtos, responsaveis, unidades, produto_nome, responsavel_nome, unidade_nome, tipo, quantidade, fornecedor, razao, data):
    try:
        # Obter IDs correspondentes
        id_produto = produtos.loc[produtos['Nome do Produto'] == produto_nome, 'ID Produto'].values[0]
        id_responsavel = responsaveis.loc[responsaveis['Nome do Responsável'] == responsavel_nome, 'ID Responsavel'].values[0]
        id_unidade = unidades.loc[unidades['Nome da Unidade'] == unidade_nome, 'ID Unidade'].values[0]
        
        # Atualizar a quantidade em estoque
        if tipo == "Entrada":
            produtos.loc[produtos['ID Produto'] == id_produto, 'Quantidade em Estoque'] += quantidade
        elif tipo == "Saída":
            produtos.loc[produtos['ID Produto'] == id_produto, 'Quantidade em Estoque'] -= quantidade
        
        # Criar nova movimentação
        nova_movimentacao = {
            'ID Produto': id_produto,
            'ID Responsavel': id_responsavel,
            'ID Unidade': id_unidade,
            'Tipo': tipo,
            'Quantidade': quantidade,
            'Fornecedor': fornecedor,
            'Razão': razao,
            'Data': data
        }
        movimentacoes = pd.concat([movimentacoes, pd.DataFrame([nova_movimentacao])], ignore_index=True)
        return movimentacoes, produtos
    except Exception as e:
        st.error(f"Erro ao adicionar movimentação: {e}")
        return movimentacoes, produtos

# Função para verificar o login
def verificar_login(username, senha, usuarios):
    try:
        # Verificar se as colunas necessárias existem
        if 'username' not in usuarios.columns or 'senha' not in usuarios.columns:
            st.error("As colunas 'username' e 'senha' não foram encontradas no DataFrame 'usuarios'.")
            return None
        
        # Verificar o login
        usuario = usuarios.loc[(usuarios['username'].str.strip() == username.strip()) & 
                               (usuarios['senha'].astype(str).str.strip() == senha.strip())]
        
        if not usuario.empty:
            return usuario.iloc[0]['nivel_acesso']
        return None
    except Exception as e:
        st.error(f"Erro ao verificar login: {e}")
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
def pagina_editar(movimentacoes, produtos, responsaveis, unidades):
    st.title("Editar")
    menu()  # Adicionar o menu aqui

    # Selecionar a ação (Adicionar, Editar, Excluir)
    acao = st.radio("Selecione a ação:", ["Adicionar", "Editar", "Excluir"])

    if acao == "Adicionar":
        with st.form("form_adicionar"):
            st.markdown("### Adicionar Novo Item")
            id_produto = st.number_input("ID do Produto", min_value=1, step=1)
            nome_produto = st.text_input("Nome do Produto")
            quantidade_estoque = st.number_input("Quantidade em Estoque", min_value=0)
            unidade_medida = st.text_input("Unidade de Medida")
            categoria = st.text_input("Categoria")

            if st.form_submit_button("Adicionar"):
                if id_produto in produtos['ID Produto'].values:
                    st.error("Erro: ID já existente.")
                else:
                    produtos = adicionar_produto(produtos, nome_produto, id_produto, quantidade_estoque, unidade_medida, categoria)
                    salvar_planilhas(movimentacoes, produtos, responsaveis, unidades, st.session_state['usuarios'])
                    st.success("Produto adicionado com sucesso!")
                    time.sleep(1)  # Delay de 1 segundo
                    st.cache_data.clear()  # Limpar o cache
                    st.rerun()  # Recarregar a página

    elif acao == "Editar":
        with st.form("form_editar"):
            st.markdown("### Editar Item Existente")
            # Selecionar o produto a ser editado
            produto_selecionado = st.selectbox("Selecione o produto para editar", produtos['Nome do Produto'].unique())
            
            # Obter os dados atuais do produto selecionado
            produto_info = produtos[produtos['Nome do Produto'] == produto_selecionado].iloc[0]
            
            # Preencher os campos com as informações atuais
            id_produto = st.number_input("ID do Produto", value=int(produto_info['ID Produto']), disabled=True)
            nome_produto = st.text_input("Nome do Produto", value=produto_info['Nome do Produto'])
            quantidade_estoque = st.number_input("Quantidade em Estoque", value=int(produto_info['Quantidade em Estoque']))
            unidade_medida = st.text_input("Unidade de Medida", value=produto_info['Unidade de Medida'])
            categoria = st.text_input("Categoria", value=produto_info['Categoria'])

            if st.form_submit_button("Editar"):
                produtos = editar_produto(produtos, id_produto, nome_produto, quantidade_estoque, unidade_medida, categoria)
                salvar_planilhas(movimentacoes, produtos, responsaveis, unidades, st.session_state['usuarios'])
                st.success("Produto editado com sucesso!")
                time.sleep(1)  # Delay de 1 segundo
                st.cache_data.clear()  # Limpar o cache
                st.rerun()  # Recarregar a página

    elif acao == "Excluir":
        with st.form("form_excluir"):
            st.markdown("### Excluir Item Existente")
            # Selecionar o produto a ser excluído
            produto_selecionado = st.selectbox("Selecione o produto para excluir", produtos['Nome do Produto'].unique())
            
            # Exibir as informações do produto selecionado
            produto_info = produtos[produtos['Nome do Produto'] == produto_selecionado].iloc[0]
            st.write(f"**ID do Produto:** {produto_info['ID Produto']}")
            st.write(f"**Nome do Produto:** {produto_info['Nome do Produto']}")
            st.write(f"**Quantidade em Estoque:** {produto_info['Quantidade em Estoque']}")
            st.write(f"**Unidade de Medida:** {produto_info['Unidade de Medida']}")
            st.write(f"**Categoria:** {produto_info['Categoria']}")

            if st.form_submit_button("Excluir"):
                produtos = excluir_produto(produtos, produto_info['ID Produto'])
                salvar_planilhas(movimentacoes, produtos, responsaveis, unidades, st.session_state['usuarios'])
                st.success("Produto excluído com sucesso!")
                time.sleep(1)  # Delay de 1 segundo
                st.cache_data.clear()  # Limpar o cache
                st.rerun()  # Recarregar a página

    # Botão para voltar à página principal
    if st.button("Voltar à Página Principal"):
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
        historico_filtrado[['Nome do Produto', 'Nome do Responsável', 'Nome da Unidade', 'Tipo', 'Quantidade', 'Fornecedor', 'Razão', 'Data']],
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

# Página de Responsáveis e Unidades
def pagina_responsaveis_unidades(responsaveis, unidades):
    st.title("Responsáveis e Unidades")
    menu()  # Adicionar o menu aqui

    # Função para gerar o próximo ID disponível
    def proximo_id(df, coluna_id):
        if df.empty:
            return 1
        else:
            return df[coluna_id].max() + 1

    # Função para adicionar responsável
    def adicionar_responsavel(responsaveis, nome_responsavel, id_unidade, cargo, telefone):
        novo_id = proximo_id(responsaveis, 'ID Responsavel')  # Gera o próximo ID
        novo_responsavel = {
            'ID Responsavel': novo_id,
            'Nome do Responsável': nome_responsavel,
            'ID Unidade': id_unidade,
            'Cargo': cargo,
            'Telefone': telefone
        }
        responsaveis = pd.concat([responsaveis, pd.DataFrame([novo_responsavel])], ignore_index=True)
        return responsaveis

    # Função para editar responsável
    def editar_responsavel(responsaveis, nome_antigo, nome_novo, id_unidade, cargo, telefone):
        responsaveis.loc[responsaveis['Nome do Responsável'] == nome_antigo, 'Nome do Responsável'] = nome_novo
        responsaveis.loc[responsaveis['Nome do Responsável'] == nome_novo, 'ID Unidade'] = id_unidade
        responsaveis.loc[responsaveis['Nome do Responsável'] == nome_novo, 'Cargo'] = cargo
        responsaveis.loc[responsaveis['Nome do Responsável'] == nome_novo, 'Telefone'] = telefone
        return responsaveis

    # Função para excluir responsável
    def excluir_responsavel(responsaveis, nome_responsavel):
        responsaveis = responsaveis[responsaveis['Nome do Responsável'] != nome_responsavel]
        return responsaveis

    # Função para adicionar unidade
    def adicionar_unidade(unidades, nome_unidade, endereco, cidade, estado):
        novo_id = proximo_id(unidades, 'ID Unidade')  # Gera o próximo ID
        nova_unidade = {
            'ID Unidade': novo_id,
            'Nome da Unidade': nome_unidade,
            'Endereço': endereco,
            'Cidade': cidade,
            'Estado': estado
        }
        unidades = pd.concat([unidades, pd.DataFrame([nova_unidade])], ignore_index=True)
        return unidades

    # Função para editar unidade
    def editar_unidade(unidades, nome_antigo, nome_novo, endereco, cidade, estado):
        unidades.loc[unidades['Nome da Unidade'] == nome_antigo, 'Nome da Unidade'] = nome_novo
        unidades.loc[unidades['Nome da Unidade'] == nome_novo, 'Endereço'] = endereco
        unidades.loc[unidades['Nome da Unidade'] == nome_novo, 'Cidade'] = cidade
        unidades.loc[unidades['Nome da Unidade'] == nome_novo, 'Estado'] = estado
        return unidades

    # Função para excluir unidade
    def excluir_unidade(unidades, nome_unidade):
        unidades = unidades[unidades['Nome da Unidade'] != nome_unidade]
        return unidades

    # Botões para responsáveis
    st.markdown("### Responsáveis")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕", key="btn_add_responsavel"):
            st.session_state['mostrar_adicionar_responsavel'] = True
            st.session_state['mostrar_editar_responsavel'] = False
            st.session_state['mostrar_excluir_responsavel'] = False
    with col2:
        if st.button("✏️", key="btn_editar_responsavel"):
            st.session_state['mostrar_adicionar_responsavel'] = False
            st.session_state['mostrar_editar_responsavel'] = True
            st.session_state['mostrar_excluir_responsavel'] = False
    with col3:
        if st.button("🗑️", key="btn_excluir_responsavel"):
            st.session_state['mostrar_adicionar_responsavel'] = False
            st.session_state['mostrar_editar_responsavel'] = False
            st.session_state['mostrar_excluir_responsavel'] = True

    # Formulário para adicionar responsável
    if st.session_state.get('mostrar_adicionar_responsavel', False):
        with st.form("form_adicionar_responsavel"):
            st.markdown("#### Adicionar Responsável")
            nome_responsavel = st.text_input("Nome do Responsável", key="nome_responsavel_add")
            id_unidade = st.number_input("ID da Unidade", min_value=1, key="id_unidade_add")
            cargo = st.text_input("Cargo", key="cargo_add")
            telefone = st.text_input("Telefone", key="telefone_add")
            if st.form_submit_button("Adicionar"):
                responsaveis = adicionar_responsavel(responsaveis, nome_responsavel, id_unidade, cargo, telefone)
                salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], responsaveis, st.session_state['unidades'], st.session_state['usuarios'])
                st.success("Responsável adicionado com sucesso!")
                st.session_state['mostrar_adicionar_responsavel'] = False
                st.cache_data.clear()  # Limpar o cache
                st.rerun()  # Recarregar a página

    # Formulário para editar responsável
    if st.session_state.get('mostrar_editar_responsavel', False):
        with st.form("form_editar_responsavel"):
            st.markdown("#### Editar Responsável")
            nome_antigo = st.selectbox("Selecione o responsável para editar", responsaveis['Nome do Responsável'].unique(), key="nome_antigo_edit")
            nome_novo = st.text_input("Novo Nome do Responsável", key="nome_novo_edit")
            id_unidade = st.number_input("Novo ID da Unidade", min_value=1, key="id_unidade_edit")
            cargo = st.text_input("Novo Cargo", key="cargo_edit")
            telefone = st.text_input("Novo Telefone", key="telefone_edit")
            if st.form_submit_button("Editar"):
                responsaveis = editar_responsavel(responsaveis, nome_antigo, nome_novo, id_unidade, cargo, telefone)
                salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], responsaveis, st.session_state['unidades'], st.session_state['usuarios'])
                st.success("Responsável editado com sucesso!")
                st.session_state['mostrar_editar_responsavel'] = False
                st.cache_data.clear()  # Limpar o cache
                st.rerun()  # Recarregar a página

    # Formulário para excluir responsável
    if st.session_state.get('mostrar_excluir_responsavel', False):
        with st.form("form_excluir_responsavel"):
            st.markdown("#### Excluir Responsável")
            nome_responsavel = st.selectbox("Selecione o responsável para excluir", responsaveis['Nome do Responsável'].unique(), key="nome_responsavel_excluir")
            if st.form_submit_button("Excluir"):
                responsaveis = excluir_responsavel(responsaveis, nome_responsavel)
                salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], responsaveis, st.session_state['unidades'], st.session_state['usuarios'])
                st.success("Responsável excluído com sucesso!")
                st.session_state['mostrar_excluir_responsavel'] = False
                st.cache_data.clear()  # Limpar o cache
                st.rerun()  # Recarregar a página

    # Exibir lista de responsáveis
    st.dataframe(
        responsaveis,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID Responsavel": "ID",
            "Nome do Responsável": "Responsável",
            "ID Unidade": "Unidade",
            "Cargo": "Cargo",
            "Telefone": "Telefone"
        }
    )

    # Botões para unidades
    st.markdown("### Unidades")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕", key="btn_add_unidade"):
            st.session_state['mostrar_adicionar_unidade'] = True
            st.session_state['mostrar_editar_unidade'] = False
            st.session_state['mostrar_excluir_unidade'] = False
    with col2:
        if st.button("✏️", key="btn_editar_unidade"):
            st.session_state['mostrar_adicionar_unidade'] = False
            st.session_state['mostrar_editar_unidade'] = True
            st.session_state['mostrar_excluir_unidade'] = False
    with col3:
        if st.button("🗑️", key="btn_excluir_unidade"):
            st.session_state['mostrar_adicionar_unidade'] = False
            st.session_state['mostrar_editar_unidade'] = False
            st.session_state['mostrar_excluir_unidade'] = True

    # Formulário para adicionar unidade
    if st.session_state.get('mostrar_adicionar_unidade', False):
        with st.form("form_adicionar_unidade"):
            st.markdown("#### Adicionar Unidade")
            nome_unidade = st.text_input("Nome da Unidade", key="nome_unidade_add")
            endereco = st.text_input("Endereço", key="endereco_add")
            cidade = st.text_input("Cidade", key="cidade_add")
            estado = st.text_input("Estado", key="estado_add")
            if st.form_submit_button("Adicionar"):
                unidades = adicionar_unidade(unidades, nome_unidade, endereco, cidade, estado)
                salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], st.session_state['responsaveis'], unidades, st.session_state['usuarios'])
                st.success("Unidade adicionada com sucesso!")
                st.session_state['mostrar_adicionar_unidade'] = False
                st.cache_data.clear()  # Limpar o cache
                st.rerun()  # Recarregar a página

    # Formulário para editar unidade
    if st.session_state.get('mostrar_editar_unidade', False):
        with st.form("form_editar_unidade"):
            st.markdown("#### Editar Unidade")
            nome_antigo = st.selectbox("Selecione a unidade para editar", unidades['Nome da Unidade'].unique(), key="nome_antigo_edit_unidade")
            nome_novo = st.text_input("Novo Nome da Unidade", key="nome_novo_edit_unidade")
            endereco = st.text_input("Novo Endereço", key="endereco_edit_unidade")
            cidade = st.text_input("Nova Cidade", key="cidade_edit_unidade")
            estado = st.text_input("Novo Estado", key="estado_edit_unidade")
            if st.form_submit_button("Editar"):
                unidades = editar_unidade(unidades, nome_antigo, nome_novo, endereco, cidade, estado)
                salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], st.session_state['responsaveis'], unidades, st.session_state['usuarios'])
                st.success("Unidade editada com sucesso!")
                st.session_state['mostrar_editar_unidade'] = False
                st.cache_data.clear()  # Limpar o cache
                st.rerun()  # Recarregar a página

    # Formulário para excluir unidade
    if st.session_state.get('mostrar_excluir_unidade', False):
        with st.form("form_excluir_unidade"):
            st.markdown("#### Excluir Unidade")
            nome_unidade = st.selectbox("Selecione a unidade para excluir", unidades['Nome da Unidade'].unique(), key="nome_unidade_excluir")
            if st.form_submit_button("Excluir"):
                unidades = excluir_unidade(unidades, nome_unidade)
                salvar_planilhas(st.session_state['movimentacoes'], st.session_state['produtos'], st.session_state['responsaveis'], unidades, st.session_state['usuarios'])
                st.success("Unidade excluída com sucesso!")
                st.session_state['mostrar_excluir_unidade'] = False
                st.cache_data.clear()  # Limpar o cache
                st.rerun()  # Recarregar a página

    # Exibir lista de unidades
    st.dataframe(
        unidades,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ID Unidade": "ID",
            "Nome da Unidade": "Unidade",
            "Endereço": "Endereço",
            "Cidade": "Cidade",
            "Estado": "Estado"
        }
    )

    # Botão para voltar à página principal
    if st.button("Voltar à Página Principal", key="btn_voltar_principal"):
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

# Executar o aplicativo
if __name__ == "__main__":
    main()