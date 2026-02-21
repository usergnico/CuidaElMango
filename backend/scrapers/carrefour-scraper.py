import sys
import os

# Agregar path del backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_supabase_admin
from datetime import datetime
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re

supabase = get_supabase_admin()

# TODAS las secciones
SECCIONES = {
    'almacen': 'https://www.carrefour.com.ar/almacen',
    'desayuno': 'https://www.carrefour.com.ar/desayuno-y-merienda',
    'bebidas': 'https://www.carrefour.com.ar/bebidas',
    'lacteos': 'https://www.carrefour.com.ar/lacteos-y-productos-frescos',
    'carnes': 'https://www.carrefour.com.ar/carnes-y-pescados',
    'frutas': 'https://www.carrefour.com.ar/frutas-y-verduras',
    'congelados': 'https://www.carrefour.com.ar/congelados',
    'panaderia': 'https://www.carrefour.com.ar/panaderia',
    'limpieza': 'https://www.carrefour.com.ar/limpieza',
    'perfumeria': 'https://www.carrefour.com.ar/perfumeria-y-farmacia',
    'hogar': 'https://www.carrefour.com.ar/hogar',
    'bazar': 'https://www.carrefour.com.ar/bazar-y-textil',
    'electronica': 'https://www.carrefour.com.ar/electro-y-tecnologia',
    'mascotas': 'https://www.carrefour.com.ar/mascotas',
    'bebe': 'https://www.carrefour.com.ar/mundo-bebe',
}

PROMOTION_KEYWORDS = ['OFF', '%', '2DO', 'PROMO', 'DESCUENTO', 'OFERTA']


def limpiar_texto(texto):
    if not texto:
        return ""
    return re.sub(r'\s+', ' ', texto).strip()


def extraer_promocion(item):
    for tag in item.find_all(['span', 'div']):
        texto = limpiar_texto(tag.text)
        if len(texto) > 50:
            continue
        if any(keyword in texto.upper() for keyword in PROMOTION_KEYWORDS):
            return texto
    return "Precio Regular"


def extraer_imagen_url(item):
    """Extrae URL de la imagen del producto"""
    try:
        img = item.find('img')
        if img and img.get('src'):
            return img['src']
        return None
    except:
        return None


def guardar_producto(nombre, precio, promo, categoria, url, imagen_url):
    """
    Guarda producto en Supabase.
    Usa service_role key (bypasea RLS).
    """
    try:
        # Limpiar precio
        if isinstance(precio, str):
            precio = precio.replace('$', '').replace('.', '').replace(',', '.').replace('\xa0', '').strip()
        
        if not precio or precio == '':
            return
        
        precio_float = float(precio)
        if precio_float <= 0:
            return
        
        # Upsert en Supabase
        data = {
            "nombre": nombre,
            "tienda": "Carrefour",
            "categoria": categoria,
            "precio": precio_float,
            "promo": promo,
            "url": url,
            "imagen_url": imagen_url,
            "ultima_actualizacion": datetime.now().isoformat()
        }
        
        # Upsert (insert o update si ya existe)
        supabase.table("productos").upsert(
            data,
            on_conflict="nombre,tienda"
        ).execute()
        
        print(f"✅ {nombre} - ${precio_float}")
        
    except Exception as e:
        print(f"❌ Error guardando {nombre}: {e}")


def extraer_datos_producto(item, categoria):
    try:
        # Nombre
        nombre_elem = item.find('span', class_='vtex-product-summary-2-x-productBrand')
        if not nombre_elem:
            return None
        nombre = limpiar_texto(nombre_elem.text)
        
        # Precio
        precio_elem = item.find('span', class_='valtech-carrefourar-product-price-0-x-currencyContainer')
        if not precio_elem:
            return None
        precio = limpiar_texto(precio_elem.text)
        
        if not precio or precio == '':
            return None
        
        # Promo
        promo = extraer_promocion(item)
        
        # URL de la imagen
        imagen_url = extraer_imagen_url(item)
        
        return (nombre, precio, promo, imagen_url)
        
    except Exception as e:
        return None


def procesar_pagina(page, categoria, num_pagina, url_base):
    url = f'{url_base}?page={num_pagina}'
    print(f"🔎 [{categoria}] Página {num_pagina}...")
    
    try:
        page.goto(url, wait_until='networkidle', timeout=60000)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        
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
        print(f"🔥 Error en página {num_pagina}: {e}")
        return -1


def scrapear_seccion(browser, categoria, url_base, max_paginas=None):
    print(f"\n{'='*60}")
    print(f"🛒 Scrapeando: {categoria.upper()}")
    print(f"{'='*60}\n")
    
    page = browser.new_page()
    num_pagina = 1
    total_productos = 0
    
    while True:
        if max_paginas and num_pagina > max_paginas:
            break
        
        productos = procesar_pagina(page, categoria, num_pagina, url_base)
        
        if productos == 0 or productos == -1:
            break
        
        total_productos += productos
        num_pagina += 1
    
    page.close()
    print(f"✅ Total: {total_productos} productos\n")
    return total_productos


def run(secciones=None, max_paginas_por_seccion=None):
    if secciones is None:
        secciones = list(SECCIONES.keys())
    
    print(f"🎯 Secciones: {', '.join(secciones)}\n")
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        
        total_general = 0
        for seccion in secciones:
            url = SECCIONES[seccion]
            total = scrapear_seccion(browser, seccion, url, max_paginas_por_seccion)
            total_general += total
        
        browser.close()
    
    print(f"\n{'='*60}")
    print(f"🎉 SCRAPING COMPLETO")
    print(f"✅ Total: {total_general} productos")
    print(f"{'='*60}")


if __name__ == "__main__":
    
    run()
