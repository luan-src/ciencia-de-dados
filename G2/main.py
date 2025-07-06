import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import urllib.request

# Configuração inicial
df = pd.read_csv("campeonato-brasileiro.csv")
df['data'] = pd.to_datetime(df['data'], dayfirst=True)
st.sidebar.header("Filtros")
estado = st.sidebar.multiselect("Estado (Mandante ou Visitante)", 
                                 options=sorted(set(df['mandante_Estado']).union(set(df['visitante_Estado']))))
rodadas = st.sidebar.slider("Rodadas", int(df['rodada'].min()), int(df['rodada'].max()), (1, 10))
datas = st.sidebar.date_input("Período", value=(df['data'].min(), df['data'].max()))
times = st.sidebar.multiselect("Time", sorted(set(df['mandante']).union(set(df['visitante']))))

# Aplicação dos filtros
data_inicio = pd.to_datetime(datas[0])
data_fim = pd.to_datetime(datas[1])
filtro = (df['rodada'].between(*rodadas)) & (df['data'].between(data_inicio, data_fim))
if estado:
    filtro &= df['mandante_Estado'].isin(estado) | df['visitante_Estado'].isin(estado)
if times:
    filtro &= df['mandante'].isin(times) | df['visitante'].isin(times)

df_filtrado = df[filtro]

if df_filtrado.empty:
    st.warning("Nenhum dado encontrado com os filtros selecionados.")
    st.stop()

# Tabs principais
tabs = st.tabs(["Resumo Geral", "Análise por Estado", "Desempenho por Time", 
                "Comparativo", "Formações e Técnicos", "Jogos Por Estado", "Média de Gols por Jogo"])

with tabs[0]:
    st.header("Resumo Geral")
    resultados = df_filtrado['vencedor'].replace('-', 'Empate').value_counts().reset_index()
    resultados.columns = ['Resultado', 'Quantidade']

    fig1 = px.pie(resultados, names='Resultado', values='Quantidade', hole=0.4,
                  title="Distribuição de Resultados")
    st.plotly_chart(fig1)

    st.subheader("Gols por rodada")
    gols = df_filtrado.groupby('rodada')[['mandante_Placar','visitante_Placar']].sum()
    gols['total'] = gols['mandante_Placar'] + gols['visitante_Placar']
    fig2 = px.line(gols.reset_index(), x='rodada', y='total', markers=True,
                   title='Total de Gols por Rodada')
    st.plotly_chart(fig2)


with tabs[1]:
    st.header("Jogos por Estado")
    estados = pd.concat([df_filtrado['mandante_Estado'], df_filtrado['visitante_Estado']])
    estado_counts = estados.value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Jogos']

    fig3 = px.bar(estado_counts, x='Estado', y='Jogos',
                  labels={'Estado': 'Estado', 'Jogos': 'Número de Jogos'},
                  title='Jogos por Estado')
    st.plotly_chart(fig3)


with tabs[2]:
    st.header("Desempenho por Time")
    time_select = st.selectbox("Selecione um time", sorted(set(df['mandante']).union(set(df['visitante']))))
    df_time = df_filtrado[(df_filtrado['mandante'] == time_select) | (df_filtrado['visitante'] == time_select)]
    df_time = df_time.sort_values("rodada")
    df_time['pontos'] = df_time.apply(lambda row: 3 if row['vencedor'] == time_select else 1 if row['vencedor'] == '-' else 0, axis=1)
    df_time['acumulado'] = df_time['pontos'].cumsum()
    fig4 = px.line(df_time, x='rodada', y='acumulado', title=f"Pontuação acumulada: {time_select}", markers=True)
    st.plotly_chart(fig4)

with tabs[3]:
    st.header("Comparativo entre Times")

    todos_times = sorted(set(df['mandante']).union(set(df['visitante'])))
    times_cmp = st.multiselect("Escolha dois times para comparar vitórias", todos_times, max_selections=2)

    if len(times_cmp) == 2:
        time1, time2 = times_cmp

        # Filtra jogos com qualquer um dos dois times
        jogos_cmp = df_filtrado[
            (df_filtrado['mandante'].isin(times_cmp)) | (df_filtrado['visitante'].isin(times_cmp))
        ]

        # Conta vitórias de cada um
        vitorias = jogos_cmp['vencedor'].value_counts().reset_index()
        vitorias.columns = ['Time', 'Vitorias']

        # Filtra apenas os dois times escolhidos
        vitorias = vitorias[vitorias['Time'].isin(times_cmp)]

        fig5 = px.bar(vitorias, x='Time', y='Vitorias',
                      title=f'Vitórias: {time1} vs {time2}',
                      color='Time', text='Vitorias')
        fig5.update_traces(textposition='outside')
        st.plotly_chart(fig5)


with tabs[4]:
    st.header("Formações mais comuns")
    form_m = df_filtrado['formacao_mandante'].value_counts().head(10)
    form_v = df_filtrado['formacao_visitante'].value_counts().head(10)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Mandante")
        st.bar_chart(form_m)
    with col2:
        st.subheader("Visitante")
        st.bar_chart(form_v)

with tabs[5]:
    st.header("Jogos por Estado")

    estados = pd.concat([df_filtrado['mandante_Estado'], df_filtrado['visitante_Estado']])
    estado_counts = estados.value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Jogos']

    fig6 = px.bar(estado_counts.sort_values(by='Jogos', ascending=True),
                  x='Jogos', y='Estado',
                  orientation='h',
                  labels={'Jogos': 'Número de Jogos', 'Estado': 'Estado'},
                  title='Número de Jogos por Estado (Mandante ou Visitante)')
    st.plotly_chart(fig6)


with tabs[6]:
    st.header("Média de Gols por Jogo")
    jogos_por_rodada = df_filtrado.groupby('rodada').size()
    gols_totais = df_filtrado.groupby('rodada')[['mandante_Placar', 'visitante_Placar']].sum()
    gols_totais['gols'] = gols_totais['mandante_Placar'] + gols_totais['visitante_Placar']
    gols_totais['media'] = gols_totais['gols'] / jogos_por_rodada
    fig7 = px.bar(gols_totais.reset_index(), x='rodada', y='media',
                  title="Média de Gols por Jogo por Rodada",
                  labels={'media': 'Média de Gols'})
    st.plotly_chart(fig7)