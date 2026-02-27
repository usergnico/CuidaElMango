import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_supabase_admin
from utils import extraer_atributos_producto
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

supabase = get_supabase_admin()

# ============================================
# SECCIONES COMPLETAS DE DISCO
# ============================================
SECCIONES = {
    # Alimentación
    'almacen': 'https://www.disco.com.ar/almacen',
    'bebidas': 'https://www.disco.com.ar/bebidas',
    'lacteos': 'https://www.disco.com.ar/lacteos',
    'carnes': 'https://www.disco.com.ar/carnes',
    'frutas': 'https://www.disco.com.ar/frutas-y-verduras',
    'quesos': 'https://www.disco.com.ar/quesos-y-fiambres',
    'congelados': 'https://www.disco.com.ar/congelados',
    'panaderia': 'https://www.disco.com.ar/panaderia-y-reposteria',
    'pastas': 'https://www.disco.com.ar/pastas-frescas',
    'rotiseria': 'https://www.disco.com.ar/rotiseria',
    
    # Limpieza y cuidado
    'limpieza': 'https://www.disco.com.ar/limpieza',
    'perfumeria': 'https://www.disco.com.ar/perfumeria',
    
    # Bebés y mascotas
    'bebe': 'https://www.disco.com.ar/mundo-bebe',
    'mascotas': 'https://www.disco.com.ar/mascotas',
    
    # Hogar y otros
    'hogar': 'https://www.disco.com.ar/hogar-y-textil',
    'electro': 'https://www.disco.com.ar/electro',
    'tiempo_libre': 'https://www.disco.com.ar/tiempo-libre',
}

def limpiar_texto(texto):
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()

def extraer_promocion(item):
    PROMOTION_KEYWORDS = ['OFF', '%', '2DO', 'PROMO', 'DESCUENTO', 'OFERTA']
    for tag in item.find_all(['span', 'div']):
        texto = limpiar_texto(tag.text)
        if len(texto) > 50:
            continue
        if any(keyword in texto.upper() for keyword in PROMOTION_KEYWORDS):
            return texto
    return "Precio Regular"

def extraer_imagen_url(item):
    try:
        img = item.find('img')
        if img and img.get('src'):
            return img['src']
        return None
    except:
        return None

def guardar_producto(nombre, precio, promo, categoria, url, imagen_url):
    """Guarda producto con atributos extraídos"""
    try:
        if isinstance(precio, str):
            precio = precio.replace('$', '').replace('.', '').replace(',', '.').replace('\xa0', '').strip()
        
        if not precio or precio == '':
            return
        
        precio_float = float(precio)
        if precio_float <= 0:
            return
        
        # EXTRAER ATRIBUTOS
        atributos = extraer_atributos_producto(nombre)
        
        data = {
            "nombre": nombre,
            "nombre_limpio": atributos['nombre_limpio'],
            "marca": atributos['marca'],
            "peso": atributos['peso'],
            "peso_unidad": atributos['peso_unidad'],
            "cantidad_unidades": atributos['cantidad_unidades'],
            "variante": atributos['variante'],
            "tienda": "Disco",
            "categoria": categoria,
            "precio": precio_float,
            "promo": promo,
            "url": url,
            "imagen_url": imagen_url,
            "ultima_actualizacion": datetime.now().isoformat()
        }
        
        supabase.table("productos").upsert(data, on_conflict="nombre,tienda").execute()
        
        marca_str = f"[{atributos['marca']}]" if atributos['marca'] else ""
        peso_str = f"{atributos['peso']}{atributos['peso_unidad']}" if atributos['peso'] else ""
        print(f"✅ {marca_str} {nombre[:40]}... {peso_str} - ${precio_float}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def extraer_datos_producto(item, categoria):
    try:
        # Nombre
        nombre_elem = item.find('span', class_='vtex-product-summary-2-x-productBrand')
        if not nombre_elem:
            return None
        nombre = limpiar_texto(nombre_elem.text)
        
        # Precio (selector específico de Disco)
        precio_elem = item.find('div', class_='discoargentina-store-theme-1dCOMij_MzTzZOCohX1K7w')
        if not precio_elem:
            # Intentar selector alternativo
            precio_elem = item.find('span', class_='discoargentina-store-theme-1uDe_0RBpvBnVBbLBqDmN9')
        
        if not precio_elem:
            return None
        
        precio = limpiar_texto(precio_elem.text)
        
        if not precio:
            return None
        
        promo = extraer_promocion(item)
        imagen_url = extraer_imagen_url(item)
        
        return (nombre, precio, promo, imagen_url)
    except:
        return None

def procesar_pagina(page, categoria, num_pagina, url_base):
    url = f'{url_base}?page={num_pagina}'
    print(f"🔎 [{categoria}] Página {num_pagina}...")
    
    try:
        page.goto(url, wait_until='domcontentloaded', timeout=60000)
        page.wait_for_selector('article', timeout=20000)
        
        # Scroll progresivo
        for i in range(5):
            page.evaluate(f"window.scrollBy(0, {i * 500})")
            page.wait_for_timeout(500)
        
        html = page.content()
        soup = BeautifulSoup(html, 'html.parser')
        items = soup.find_all('article')
        
        if not items:
            return 0
        
        productos_encontrados = 0
        for item in items:
            datos = extraer_datos_producto(item, categoria)
            if datos:
                nombre, precio, promo, imagen_url = datos
                guardar_producto(nombre, precio, promo, categoria, url, imagen_url)
                productos_encontrados += 1
        
        return productos_encontrados
    except Exception as e:
        print(f"🔥 Error: {e}")
        return -1

def scrapear_seccion(browser, categoria, url_base, max_paginas=None):
    print(f"\n{'='*60}")
    print(f"🛍️ {categoria.upper()}")
    print(f"{'='*60}\n")
    
    page = browser.new_page()
    num_pagina = 1
    total_productos = 0
    
    while True:
        if max_paginas and num_pagina > max_paginas:
            break
        
        productos = procesar_pagina(page, categoria, num_pagina, url_base)
        if productos <= 0:
            break
        
        total_productos += productos
        num_pagina += 1
    
    page.close()
    print(f"✅ Total: {total_productos}\n")
    return total_productos

def run(secciones=None, max_paginas_por_seccion=None):
    if secciones is None:
        secciones = list(SECCIONES.keys())
    
    print(f"\n{'='*60}")
    print(f"🛍️ DISCO - Scraping")
    print(f"Secciones: {len(secciones)}")
    print(f"{'='*60}\n")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        page = context.new_page()
        page.close()
        
        total = 0
        for seccion in secciones:
            if seccion in SECCIONES:
                total += scrapear_seccion(browser, seccion, SECCIONES[seccion], max_paginas_por_seccion)
            else:
                print(f"⚠️  Sección '{seccion}' no existe")
        
        browser.close()
    
    print(f"\n{'='*60}")
    print(f"🎉 DISCO - Total: {total} productos")
    print(f"{'='*60}\n")
    
    return total

if __name__ == "__main__":
    # Para producción completa
    run()
