import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Configuração inicial
df = pd.read_csv("campeonato-brasileiro.csv")
df['data'] = pd.to_datetime(df['data'], dayfirst=True)

# Sidebar - Filtros
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

# Tabs principais
tabs = st.tabs(["Resumo Geral", "Análise por Estado", "Desempenho por Time", 
                "Comparativo", "Formacoes e Tecnicos", "Mapa de Jogos"])

with tabs[0]:
    st.header("Resumo Geral")
    resultados = df_filtrado['vencedor'].value_counts()
    fig1, ax1 = plt.subplots()
    ax1.pie(resultados, labels=resultados.index, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    st.pyplot(fig1)

    st.subheader("Gols por rodada")
    gols = df_filtrado.groupby('rodada')[['mandante_Placar','visitante_Placar']].sum()
    gols['total'] = gols['mandante_Placar'] + gols['visitante_Placar']
    st.line_chart(gols['total'])

with tabs[1]:
    st.header("Jogos por Estado")
    estados = pd.concat([df_filtrado['mandante_Estado'], df_filtrado['visitante_Estado']])
    estado_counts = estados.value_counts()
    fig2, ax2 = plt.subplots()
    sns.barplot(x=estado_counts.index, y=estado_counts.values, ax=ax2)
    ax2.set_ylabel("Número de Jogos")
    ax2.set_xlabel("Estado")
    st.pyplot(fig2)

with tabs[2]:
    st.header("Desempenho por Time")
    time_select = st.selectbox("Selecione um time", sorted(set(df['mandante']).union(set(df['visitante']))))
    df_time = df_filtrado[(df_filtrado['mandante'] == time_select) | (df_filtrado['visitante'] == time_select)]
    df_time = df_time.sort_values("rodada")
    df_time['pontos'] = df_time.apply(lambda row: 3 if row['vencedor'] == time_select else 1 if row['vencedor'] == '-' else 0, axis=1)
    df_time['acumulado'] = df_time['pontos'].cumsum()
    fig3 = px.line(df_time, x='rodada', y='acumulado', title=f"Pontuação acumulada: {time_select}")
    st.plotly_chart(fig3)

with tabs[3]:
    st.header("Comparativo entre Times")
    times_cmp = st.multiselect("Escolha dois times", sorted(set(df['mandante']).union(set(df['visitante']))), max_selections=2)
    if len(times_cmp) == 2:
        fig_cmp = px.histogram(df_filtrado[df_filtrado['mandante'].isin(times_cmp) | df_filtrado['visitante'].isin(times_cmp)],
                               x="vencedor", color="vencedor", barmode='group', title="Vitórias por Time")
        st.plotly_chart(fig_cmp)

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
    st.header("Mapa de Jogos por Estado")
    mapa = pd.DataFrame({
        'estado': estados.value_counts().index,
        'jogos': estados.value_counts().values
    })
    fig_map = px.choropleth(mapa, locationmode="USA-states", locations='estado', color='jogos',
                            scope="south america", title="Distribuição de Jogos por Estado")
    st.plotly_chart(fig_map)
