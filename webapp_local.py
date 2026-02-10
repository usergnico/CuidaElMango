"""
Mini Web App Local - Comparador de Precios
Prueba local antes de subir a Railway
"""

import streamlit as st
import sqlite3
import os
import pandas as pd
from datetime import datetime
import unicodedata

# Configuración de la página
st.set_page_config(
    page_title="Comparador de Precios",
    page_icon="🛒",
    layout="wide"
)

# Rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CARREFOUR_DB = os.path.join(DATA_DIR, 'carrefour.db')
DISCO_DB = os.path.join(DATA_DIR, 'disco.db')


@st.cache_resource
def conectar(db_path):
    """Conecta a la base de datos"""
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        
        def _strip_accents(s):
            if s is None:
                return None
            nk = unicodedata.normalize('NFKD', str(s))
            return ''.join([c for c in nk if not unicodedata.combining(c)])
        
        conn.create_function('unaccent', 1, _strip_accents)
        return conn
    except Exception as e:
        st.error(f"Error conectando a DB: {e}")
        return None


def buscar_producto(conn, termino, limit=10):
    """Busca productos en la DB"""
    if not conn:
        return []
    
    try:
        def normalizar(s):
            nk = unicodedata.normalize('NFKD', str(s))
            return ''.join([c for c in nk if not unicodedata.combining(c)]).lower()
        
        pattern = f"%{normalizar(termino)}%"
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nombre, precio_actual as precio, promo_actual as promo, url, categoria "
            "FROM productos WHERE unaccent(LOWER(nombre)) LIKE ? ORDER BY nombre LIMIT ?",
            (pattern, limit)
        )
        return cursor.fetchall()
    except:
        # Fallback para DBs viejas
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, nombre, precio, promo, NULL as url, 'sin categoria' as categoria "
                "FROM productos WHERE LOWER(nombre) LIKE ? ORDER BY nombre LIMIT ?",
                (pattern, limit)
            )
            return cursor.fetchall()
        except:
            return []


def calcular_precio_con_promo(precio, promo, cantidad):
    """Calcula precio total con promociones"""
    if not promo or promo.lower() == 'precio regular':
        return precio * cantidad
    
    import re
    match = re.search(r'2DO\s+AL\s+(\d+)%|SEGUNDO\s+AL\s+(\d+)%', promo.upper())
    if match:
        descuento_pct = int(match.group(1) or match.group(2))
        precio_segundo = precio * (descuento_pct / 100.0)
        
        if cantidad == 1:
            return precio
        elif cantidad == 2:
            return precio + precio_segundo
        else:
            pares = cantidad // 2
            sobrante = cantidad % 2
            return pares * (precio + precio_segundo) + sobrante * precio
    
    return precio * cantidad


# ============================================
# INTERFAZ
# ============================================

# Header
st.title("🛒 Comparador de Precios")
st.markdown("**Compará precios entre Carrefour y Disco**")

# Conectar a DBs
conn_c = conectar(CARREFOUR_DB)
conn_d = conectar(DISCO_DB)

if not conn_c and not conn_d:
    st.error("❌ No hay bases de datos disponibles")
    st.info("💡 Ejecutá primero los scrapers o descargá las DBs")
    st.stop()

# Mostrar estado
col1, col2 = st.columns(2)
with col1:
    if conn_c:
        st.success("✅ Carrefour disponible")
    else:
        st.error("❌ Carrefour no disponible")

with col2:
    if conn_d:
        st.success("✅ Disco disponible")
    else:
        st.error("❌ Disco no disponible")

st.divider()

# Inicializar session state
if 'carrito' not in st.session_state:
    st.session_state.carrito = []

if 'historial_gastos' not in st.session_state:
    st.session_state.historial_gastos = []

# Sidebar - Agregar productos
with st.sidebar:
    st.header("🔍 Buscar Productos")
    
    busqueda = st.text_input(
        "Buscar producto",
        placeholder="Ej: arroz, aceite, fideos...",
        help="Escribí el nombre del producto"
    )
    
    if busqueda:
        st.subheader("Resultados")
        
        # Buscar en ambas tiendas
        tabs = st.tabs(["🛒 Carrefour", "🛍️ Disco"])
        
        with tabs[0]:
            if conn_c:
                resultados_c = buscar_producto(conn_c, busqueda)
                
                if resultados_c:
                    for prod_id, nombre, precio, promo, url, categoria in resultados_c:
                        with st.container():
                            st.markdown(f"**{nombre}**")
                            
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.write(f"💰 ${precio:,.2f}")
                                if promo and promo.lower() != 'precio regular':
                                    st.caption(f"🏷️ {promo}")
                            
                            with col2:
                                cantidad = st.number_input(
                                    "Cant.",
                                    min_value=1,
                                    value=1,
                                    key=f"cant_c_{prod_id}",
                                    label_visibility="collapsed"
                                )
                                
                                if st.button("➕", key=f"add_c_{prod_id}"):
                                    st.session_state.carrito.append({
                                        'tienda': 'Carrefour',
                                        'nombre': nombre,
                                        'precio': precio,
                                        'promo': promo,
                                        'cantidad': cantidad,
                                        'url': url
                                    })
                                    st.success("✅ Agregado!")
                                    st.rerun()
                            
                            st.divider()
                else:
                    st.info("No se encontraron productos")
            else:
                st.warning("Base de datos no disponible")
        
        with tabs[1]:
            if conn_d:
                resultados_d = buscar_producto(conn_d, busqueda)
                
                if resultados_d:
                    for prod_id, nombre, precio, promo, url, categoria in resultados_d:
                        with st.container():
                            st.markdown(f"**{nombre}**")
                            
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.write(f"💰 ${precio:,.2f}")
                                if promo and promo.lower() != 'precio regular':
                                    st.caption(f"🏷️ {promo}")
                            
                            with col2:
                                cantidad = st.number_input(
                                    "Cant.",
                                    min_value=1,
                                    value=1,
                                    key=f"cant_d_{prod_id}",
                                    label_visibility="collapsed"
                                )
                                
                                if st.button("➕", key=f"add_d_{prod_id}"):
                                    st.session_state.carrito.append({
                                        'tienda': 'Disco',
                                        'nombre': nombre,
                                        'precio': precio,
                                        'promo': promo,
                                        'cantidad': cantidad,
                                        'url': url
                                    })
                                    st.success("✅ Agregado!")
                                    st.rerun()
                            
                            st.divider()
                else:
                    st.info("No se encontraron productos")
            else:
                st.warning("Base de datos no disponible")

# Main - Carrito y comparación
st.header("🛒 Tu Carrito")

if not st.session_state.carrito:
    st.info("👈 Buscá y agregá productos desde el panel lateral")
else:
    # Mostrar carrito
    for i, item in enumerate(st.session_state.carrito):
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1:
            icono = "🛒" if item['tienda'] == 'Carrefour' else "🛍️"
            st.markdown(f"**{icono} {item['nombre']}**")
            if item['promo'] and item['promo'].lower() != 'precio regular':
                st.caption(f"🏷️ {item['promo']}")
        
        with col2:
            st.write(f"x{item['cantidad']}")
        
        with col3:
            st.write(f"${item['precio']:,.2f}")
        
        with col4:
            total_item = calcular_precio_con_promo(item['precio'], item['promo'], item['cantidad'])
            st.write(f"**${total_item:,.2f}**")
        
        with col5:
            if st.button("🗑️", key=f"del_{i}"):
                st.session_state.carrito.pop(i)
                st.rerun()
        
        st.divider()
    
    # Resumen por tienda
    st.subheader("💰 Resumen")
    
    por_tienda = {}
    for item in st.session_state.carrito:
        tienda = item['tienda']
        if tienda not in por_tienda:
            por_tienda[tienda] = 0
        total_item = calcular_precio_con_promo(item['precio'], item['promo'], item['cantidad'])
        por_tienda[tienda] += total_item
    
    if len(por_tienda) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            if 'Carrefour' in por_tienda:
                st.metric(
                    label="🛒 Total Carrefour",
                    value=f"${por_tienda['Carrefour']:,.2f}"
                )
        
        with col2:
            if 'Disco' in por_tienda:
                st.metric(
                    label="🛍️ Total Disco",
                    value=f"${por_tienda['Disco']:,.2f}"
                )
        
        # Recomendación
        if len(por_tienda) > 1:
            st.divider()
            tienda_ganadora = min(por_tienda, key=por_tienda.get)
            tienda_perdedora = max(por_tienda, key=por_tienda.get)
            ahorro = por_tienda[tienda_perdedora] - por_tienda[tienda_ganadora]
            porcentaje = (ahorro / por_tienda[tienda_perdedora]) * 100
            
            icono = "🛒" if tienda_ganadora == "Carrefour" else "🛍️"
            
            st.success(f"### 💡 Recomendación: Comprá en {icono} {tienda_ganadora}")
            st.info(f"💰 **Ahorrás: ${ahorro:,.2f}** ({porcentaje:.1f}%)")
        
        # Guardar gasto
        st.divider()
        if st.button("💾 Guardar este gasto", type="primary"):
            total = sum(por_tienda.values())
            st.session_state.historial_gastos.append({
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'total': total,
                'productos': len(st.session_state.carrito)
            })
            st.success("✅ Gasto guardado!")
            st.balloons()

# Tracking de gastos
if st.session_state.historial_gastos:
    st.divider()
    st.header("📊 Historial de Gastos")
    
    # Convertir a DataFrame
    df = pd.DataFrame(st.session_state.historial_gastos)
    df['fecha'] = pd.to_datetime(df['fecha'])
    
    # Gráfico
    st.line_chart(df.set_index('fecha')['total'])
    
    # Tabla
    st.dataframe(
        df[['fecha', 'productos', 'total']],
        column_config={
            'fecha': 'Fecha',
            'productos': 'Cantidad',
            'total': st.column_config.NumberColumn('Total', format="$%.2f")
        },
        hide_index=True
    )
    
    # Stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Gasto promedio", f"${df['total'].mean():,.2f}")
    with col2:
        st.metric("Total acumulado", f"${df['total'].sum():,.2f}")
    with col3:
        st.metric("Compras realizadas", len(df))

# Footer
st.divider()
st.caption("💡 Los datos se guardan localmente en tu sesión (cookies)")
st.caption("🔒 No guardamos ningún dato personal")
