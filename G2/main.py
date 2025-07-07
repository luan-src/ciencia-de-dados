import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(page_title="Dashboard Brasileirão", layout="wide")

df = pd.read_csv("G2/campeonato-brasileiro.csv")
df['data'] = pd.to_datetime(df['data'], dayfirst=True)

st.sidebar.header("Filtros")
estado = st.sidebar.multiselect("Estado (Mandante ou Visitante)",
                                options=sorted(set(df['mandante_Estado']).union(set(df['visitante_Estado']))))

rodadas = st.sidebar.slider("Rodadas", int(df['rodada'].min()), int(df['rodada'].max()), (1, 10))
datas = st.sidebar.date_input("Período", value=(df['data'].min(), df['data'].max()))
times = st.sidebar.multiselect("Time", sorted(set(df['mandante']).union(set(df['visitante']))))

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

st.title("Dashboard do Campeonato Brasileiro")
st.markdown("""
Explore os dados do campeonato com gráficos interativos e filtros inteligentes.  
Use a barra lateral para refinar sua análise.
""")

# Abas principais
tabs = st.tabs(["Resumo Geral", "Jogos por Estado", "Desempenho por Time",
                "Comparativo", "Formações", "Jogos por Estado (Horizontal)", "Média de Gols"])

with tabs[0]:
    st.header("Resumo Geral")
    st.markdown("Mostra a porcentagem de vitórias de cada time nos jogos filtrados (empates são ignorados).")

    df_vitorias = df_filtrado[df_filtrado['vencedor'] != '-']
    resultados = df_vitorias['vencedor'].value_counts(normalize=True).reset_index()
    resultados.columns = ['Time', 'Porcentagem']
    resultados['Porcentagem'] *= 100  # opcional: transformar em %

    tipo_grafico = st.radio("Tipo de gráfico:", ["Pizza", "Barra"], horizontal=True)

    if tipo_grafico == "Pizza":
        fig1 = px.pie(resultados, names='Time', values='Porcentagem', hole=0.4)
    else:
        fig1 = px.bar(resultados, x='Time', y='Porcentagem', color='Time', text='Porcentagem')
        fig1.update_traces(texttemplate='%{text:.2f}%', textposition='outside')

    st.plotly_chart(fig1, use_container_width=True)


with tabs[1]:
    st.header("Jogos por Estado")
    st.markdown("Exibe a quantidade total de jogos realizados por estado, considerando mandantes e visitantes.")

    estados = pd.concat([df_filtrado['mandante_Estado'], df_filtrado['visitante_Estado']])
    estado_counts = estados.value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Jogos']

    fig3 = px.bar(estado_counts, x='Estado', y='Jogos', color='Estado',
                  labels={'Estado': 'Estado', 'Jogos': 'Número de Jogos'})
    st.plotly_chart(fig3, use_container_width=True)

with tabs[2]:
    st.header("Desempenho por Time")
    st.markdown("Mostra a evolução da pontuação de um time ao longo das rodadas, acumulando 3 pontos por vitória e 1 por empate.")

    time_select = st.selectbox("Selecione um time", sorted(set(df['mandante']).union(set(df['visitante']))))
    df_time = df_filtrado[(df_filtrado['mandante'] == time_select) | (df_filtrado['visitante'] == time_select)]
    df_time = df_time.sort_values("rodada")
    df_time['pontos'] = df_time.apply(
        lambda row: 3 if row['vencedor'] == time_select else 1 if row['vencedor'] == '-' else 0, axis=1)
    df_time['acumulado'] = df_time['pontos'].cumsum()
    fig4 = px.line(df_time, x='rodada', y='acumulado', title=f"Pontuação acumulada: {time_select}", markers=True)
    st.plotly_chart(fig4, use_container_width=True)

with tabs[3]:
    st.header("Comparativo entre Times")
    st.markdown("Compara o número total de vitórias entre dois times selecionados dentro do filtro aplicado.")

    todos_times = sorted(set(df['mandante']).union(set(df['visitante'])))
    times_cmp = st.multiselect("Escolha dois times para comparar", todos_times, max_selections=2)

    if len(times_cmp) == 2:
        time1, time2 = times_cmp
        jogos_cmp = df_filtrado[
            (df_filtrado['mandante'].isin(times_cmp)) | (df_filtrado['visitante'].isin(times_cmp))
        ]
        vitorias = jogos_cmp['vencedor'].value_counts().reset_index()
        vitorias.columns = ['Time', 'Vitórias']
        vitorias = vitorias[vitorias['Time'].isin(times_cmp)]

        fig5 = px.bar(vitorias, x='Time', y='Vitórias', color='Time', text='Vitórias')
        fig5.update_traces(textposition='outside')
        st.plotly_chart(fig5, use_container_width=True)

with tabs[4]:
    st.header("Formações Mais Comuns")
    st.markdown("Apresenta as formações táticas mais utilizadas por times mandantes e visitantes nos jogos filtrados.")

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
    st.header("Jogos por Estado - Gráfico Horizontal")
    st.markdown("Versão alternativa do gráfico de jogos por estado, exibindo os dados em barras horizontais.")

    estados = pd.concat([df_filtrado['mandante_Estado'], df_filtrado['visitante_Estado']])
    estado_counts = estados.value_counts().reset_index()
    estado_counts.columns = ['Estado', 'Jogos']
    fig6 = px.bar(estado_counts.sort_values(by='Jogos'), x='Jogos', y='Estado', orientation='h')
    st.plotly_chart(fig6, use_container_width=True)

with tabs[6]:
    st.header("Média de Gols por Rodada")
    st.markdown("Mostra a média de gols por jogo em cada rodada, considerando gols de mandantes e visitantes.")

    jogos_por_rodada = df_filtrado.groupby('rodada').size()
    gols_totais = df_filtrado.groupby('rodada')[['mandante_Placar', 'visitante_Placar']].sum()
    gols_totais['gols'] = gols_totais['mandante_Placar'] + gols_totais['visitante_Placar']
    gols_totais['media'] = gols_totais['gols'] / jogos_por_rodada
    fig7 = px.bar(gols_totais.reset_index(), x='rodada', y='media',
                  title="Média de Gols por Jogo",
                  labels={'media': 'Média de Gols'})
    st.plotly_chart(fig7, use_container_width=True)
