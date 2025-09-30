
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import networkx as nx

st.set_page_config(page_title="ERP • WMS • TMS • IoT", layout="wide")
st.title("Explorador de Sistemas Digitales: ERP • WMS • TMS • IoT")
st.caption("Visualiza cómo cada sistema aporta datos y cómo se integran para la toma de decisiones.")

@st.cache_data
def load_defaults():
    erp_inv = pd.read_csv("sample_data/erp_inventory_master.csv")
    erp_sales = pd.read_csv("sample_data/erp_sales.csv", parse_dates=["fecha"])
    erp_purch = pd.read_csv("sample_data/erp_purchases.csv", parse_dates=["fecha"])
    wms = pd.read_csv("sample_data/wms_movements.csv", parse_dates=["fecha"])
    tms = pd.read_csv("sample_data/tms_shipments.csv", parse_dates=["fecha"])
    iot = pd.read_csv("sample_data/iot_sensors.csv", parse_dates=["timestamp"])
    return erp_inv, erp_sales, erp_purch, wms, tms, iot

erp_inv, erp_sales, erp_purch, wms, tms, iot = load_defaults()

tabs = st.tabs(["ERP","WMS","TMS","IoT","Integración (Mapa de Datos)"])

with tabs[0]:
    st.subheader("ERP")
    st.write("**Maestro de inventario** y transacciones de **ventas** y **compras**.")
    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(erp_inv)
        fig = px.bar(erp_inv, x="sku", y="stock_actual", color="categoria", title="Stock actual por SKU (ERP)")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        sales = erp_sales.groupby("fecha", as_index=False)["unidades_vendidas"].sum()
        fig2 = px.line(sales, x="fecha", y="unidades_vendidas", title="Ventas diarias (ERP)")
        st.plotly_chart(fig2, use_container_width=True)
        purch = erp_purch.groupby("fecha", as_index=False)["unidades_compradas"].sum()
        st.plotly_chart(px.line(purch, x="fecha", y="unidades_compradas", title="Compras diarias (ERP)"), use_container_width=True)

with tabs[1]:
    st.subheader("WMS")
    st.write("Movimientos de almacén: **entradas, salidas, tiempos de picking**.")
    c1, c2 = st.columns(2)
    with c1:
        mv = wms.groupby("sku", as_index=False)[["entradas","salidas"]].sum()
        st.plotly_chart(px.bar(mv, x="sku", y=["entradas","salidas"], barmode="group", title="Entradas/Salidas por SKU (WMS)"), use_container_width=True)
    with c2:
        pick = wms.groupby("fecha", as_index=False)["tiempo_picking_min"].mean()
        st.plotly_chart(px.line(pick, x="fecha", y="tiempo_picking_min", title="Tiempo medio de picking (min)"), use_container_width=True)
    st.dataframe(wms.head(20))

with tabs[2]:
    st.subheader("TMS")
    st.write("Envíos por ruta: **entregado, coste, puntualidad**.")
    c1, c2 = st.columns(2)
    with c1:
        rt = tms.groupby("ruta", as_index=False)["entregado"].sum().sort_values("entregado", ascending=False)
        st.plotly_chart(px.bar(rt, x="ruta", y="entregado", title="Entregado por ruta (TMS)"), use_container_width=True)
    with c2:
        ontime = tms.groupby("fecha", as_index=False)["puntualidad"].mean()
        st.plotly_chart(px.line(ontime, x="fecha", y="puntualidad", title="Puntualidad media"), use_container_width=True)
    st.dataframe(tms.head(20))

with tabs[3]:
    st.subheader("IoT")
    st.write("Sensores de **planta** (temperatura, vibración) y **cadena de frío** (temperatura, GPS).")
    c1, c2 = st.columns(2)
    with c1:
        plant = iot[iot["vibracion"].notna()].copy()
        if not plant.empty:
            st.plotly_chart(px.line(plant, x="timestamp", y=["temp_o_vib","vibracion"], title="Planta: temperatura y vibración"), use_container_width=True)
    with c2:
        cold = iot[iot["vibracion"].isna()].copy()
        if not cold.empty:
            st.plotly_chart(px.line(cold, x="timestamp", y="temp_o_vib", title="Cadena de frío: temperatura"), use_container_width=True)
    st.dataframe(iot.head(20))

with tabs[4]:
    st.subheader("Integración (Mapa de Datos)")
    st.write("Relaciones típicas entre sistemas. Pasa el cursor sobre los nodos para leerlos.")
    # Simple network diagram
    G = nx.DiGraph()
    nodes = [
        ("ERP: Inventario maestro","ERP"),
        ("ERP: Ventas","ERP"),
        ("ERP: Compras","ERP"),
        ("WMS: Movimientos","WMS"),
        ("TMS: Envíos","TMS"),
        ("IoT: Planta","IoT"),
        ("IoT: Cadena de frío","IoT"),
        ("Data Lake / BI","BI"),
        ("Modelos de IA","AI"),
        ("Decisiones Ops/Log","BIZ")
    ]
    for n, _ in nodes:
        G.add_node(n)
    edges = [
        ("ERP: Inventario maestro","WMS: Movimientos"),
        ("ERP: Ventas","WMS: Movimientos"),
        ("ERP: Compras","WMS: Movimientos"),
        ("WMS: Movimientos","TMS: Envíos"),
        ("IoT: Planta","ERP: Inventario maestro"),
        ("IoT: Cadena de frío","TMS: Envíos"),
        ("ERP: Ventas","Data Lake / BI"),
        ("WMS: Movimientos","Data Lake / BI"),
        ("TMS: Envíos","Data Lake / BI"),
        ("IoT: Planta","Data Lake / BI"),
        ("IoT: Cadena de frío","Data Lake / BI"),
        ("Data Lake / BI","Modelos de IA"),
        ("Modelos de IA","Decisiones Ops/Log")
    ]
    for s,t in edges:
        G.add_edge(s,t)

    pos = nx.spring_layout(G, seed=2, k=1.2)
    edge_x, edge_y = [], []
    for s, t in G.edges():
        x0,y0 = pos[s]; x1,y1 = pos[t]
        edge_x += [x0, x1, None]; edge_y += [y0, y1, None]
    edge_trace = go.Scatter(x=edge_x, y=edge_y, line=dict(width=1), hoverinfo='none', mode='lines')

    node_x, node_y, texts = [], [], []
    for n in G.nodes():
        x,y = pos[n]; node_x.append(x); node_y.append(y); texts.append(n)
    node_trace = go.Scatter(x=node_x, y=node_y, mode='markers+text', text=texts, textposition='top center',
                            marker=dict(size=14), hoverinfo='text')

    fig = go.Figure(data=[edge_trace, node_trace])
    fig.update_layout(margin=dict(l=10,r=10,t=10,b=10), height=600)
    st.plotly_chart(fig, use_container_width=True)

st.caption("Tip: sustituye los CSV de muestra por tus propios extractos de ERP/WMS/TMS/IoT para ver tu mapa de datos real.")
