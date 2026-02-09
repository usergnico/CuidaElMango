#!/usr/bin/env python3
import sqlite3
import os
import sys
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CARREFOUR_DB = os.path.join(DATA_DIR, 'carrefour.db')
DISCO_DB = os.path.join(DATA_DIR, 'disco.db')


def conectar(db_path):
    if not os.path.exists(db_path):
        print(f"❌ Error: base de datos no encontrada: {db_path}")
        return None
    try:
        conn = sqlite3.connect(db_path)
        # Registrar función para normalizar/acento-insensible en las consultas
        def _strip_accents(s):
            if s is None:
                return None
            try:
                s = str(s)
            except Exception:
                return s
            nkfd = unicodedata.normalize('NFKD', s)
            return ''.join([c for c in nkfd if not unicodedata.combining(c)])

        conn.create_function('unaccent', 1, _strip_accents)
        return conn
    except Exception as e:
        print(f"❌ Error conectando a {db_path}: {e}")
        return None


def buscar_coincidencias(conn, termino, limit=50, strict=False):
    """Busca coincidencias en la DB.

    Si strict=True, exige que todas las palabras del término aparezcan en el nombre
    (AND de LIKE). Si no hay resultados en modo strict el llamador puede fallback.
    """
    if conn is None:
        return []
    cur = conn.cursor()
    texto = termino.lower().strip()
    if not texto:
        return []

    try:
        # Normalizamos el término para que también esté sin acentos
        def normalizar(s):
            if s is None:
                return ''
            nk = unicodedata.normalize('NFKD', str(s))
            return ''.join([c for c in nk if not unicodedata.combining(c)]).lower()

        if strict:
            words = [w for w in texto.split() if w]
            if not words:
                return []
            where_clauses = ' AND '.join(['unaccent(LOWER(nombre)) LIKE ?' for _ in words])
            params = [f"%{normalizar(w)}%" for w in words] + [limit]
            
            # Buscar en tabla nueva (precio_actual en vez de precio)
            query = f"SELECT id, nombre, precio_actual as precio, promo_actual as promo FROM productos WHERE {where_clauses} ORDER BY nombre LIMIT ?"
            cur.execute(query, params)
            return cur.fetchall()
        else:
            pattern = f"%{normalizar(texto)}%"
            cur.execute("SELECT id, nombre, precio_actual as precio, promo_actual as promo FROM productos WHERE unaccent(LOWER(nombre)) LIKE ? ORDER BY nombre LIMIT ?", (pattern, limit))
            return cur.fetchall()
    except Exception as e:
        # Fallback para DB viejas (sin precio_actual)
        try:
            if strict:
                words = [w for w in texto.split() if w]
                if not words:
                    return []
                where_clauses = ' AND '.join(['unaccent(LOWER(nombre)) LIKE ?' for _ in words])
                params = [f"%{normalizar(w)}%" for w in words] + [limit]
                query = f"SELECT id, nombre, precio, promo FROM productos WHERE {where_clauses} ORDER BY nombre LIMIT ?"
                cur.execute(query, params)
                return cur.fetchall()
            else:
                pattern = f"%{normalizar(texto)}%"
                cur.execute("SELECT id, nombre, precio, promo FROM productos WHERE unaccent(LOWER(nombre)) LIKE ? ORDER BY nombre LIMIT ?", (pattern, limit))
                return cur.fetchall()
        except Exception:
            return []


def formatear_precio(p):
    try:
        return f"${float(p):,.2f}"
    except Exception:
        return str(p)


def pedir_cantidad(nombre):
    """Pide al usuario que especifique la cantidad del producto."""
    while True:
        cant = input(f"    ¿Cuánto(s) {nombre}? (cantidad, o Enter para 1): ").strip()
        if cant == '':
            return 1
        if cant.isdigit() and int(cant) > 0:
            return int(cant)
        print("    Entrada inválida. Ingrese un número positivo.")


def calcular_precio_con_promo(precio_base, promo, cantidad):
    """
    Calcula el precio total con cantidad y aplicando descuentos si corresponde.
    
    Si la promo es "2DO AL X%", calcula: precio_base + (precio_base * X%).
    Si es otro descuento, asume que el precio ya tiene descuento aplicado.
    
    Retorna: (precio_total, precio_con_descuento_unitario)
    """
    precio_base_float = float(precio_base)
    
    if not promo or promo.lower() == 'precio regular':
        # Sin descuento: precio_base × cantidad
        return precio_base_float * cantidad, precio_base_float
    
    # Detectar "2DO AL X%", "SEGUNDO AL X%"
    import re
    match = re.search(r'2DO\s+AL\s+(\d+)%|SEGUNDO\s+AL\s+(\d+)%', promo.upper())
    if match:
        descuento_pct = int(match.group(1) or match.group(2))
        precio_segundo = precio_base_float * (descuento_pct / 100.0)
        
        if cantidad == 1:
            # Solo uno, no se aplica descuento
            return precio_base_float, precio_base_float
        elif cantidad == 2:
            # Primer producto a precio normal, segundo con descuento
            total = precio_base_float + precio_segundo
            return total, precio_segundo
        else:
            # Más de 2: parejas con descuento + lo que sobre
            pares = cantidad // 2
            sobrante = cantidad % 2
            total = pares * (precio_base_float + precio_segundo) + sobrante * precio_base_float
            return total, precio_segundo
    
    # Otros descuentos: asumir que el precio ya está con descuento
    return precio_base_float * cantidad, precio_base_float


def elegir_coincidencia(all_matches, termino):
    if not all_matches:
        print(f"  ⚠️ No se encontraron coincidencias para '{termino}' en ninguna tienda.")
        return None
    # UI mejorada: paginación y filtrado por tienda
    def mostrar_pagina(matches, page, per_page):
        start = page * per_page
        end = start + per_page
        for i, (store, row) in enumerate(matches[start:end], start=start + 1):
            _id, nombre, precio, promo = row
            store_icon = '🛒' if store.lower().startswith('car') else '🛍️'
            print(f"    {i}) {store_icon} [{store}] {nombre} — {formatear_precio(precio)} — {promo}")

    per_page = 10
    page = 0
    filtered = list(all_matches)

    print(f"  Seleccione la coincidencia correcta para '{termino}':")
    print("    Comandos: número = elegir, 'c' = filtrar Carrefour, 'd' = filtrar Disco, 'a' = mostrar todas, 'n' = siguiente, 'p' = anterior, 's' = saltar")

    while True:
        total_pages = (len(filtered) - 1) // per_page + 1 if filtered else 0
        if not filtered:
            print("    (No hay opciones para mostrar)")
        else:
            print(f"    Mostrando {len(filtered)} coincidencias (página {page+1}/{total_pages}):")
            mostrar_pagina(filtered, page, per_page)

        sel = input("    Ingrese comando: ").strip().lower()
        if sel == 's' or sel == '':
            return None
        if sel == 'c':
            filtered = [m for m in all_matches if m[0].lower().startswith('car')]
            page = 0
            continue
        if sel == 'd':
            filtered = [m for m in all_matches if m[0].lower().startswith('dis') or m[0].lower().startswith('dic')]
            page = 0
            continue
        if sel == 'a':
            filtered = list(all_matches)
            page = 0
            continue
        if sel == 'n':
            if (page + 1) * per_page < len(filtered):
                page += 1
            else:
                print("    Ya estás en la última página.")
            continue
        if sel == 'p':
            if page > 0:
                page -= 1
            else:
                print("    Ya estás en la primera página.")
            continue
        if sel.isdigit():
            idx = int(sel) - 1
            if 0 <= idx < len(filtered):
                return filtered[idx]
            else:
                print("    Número fuera de rango. Intente de nuevo.")
            continue
        print("    Entrada inválida. Intente de nuevo.")




def main():
    print("🛒 Script de comparación de carrito — busca en Carrefour y Disco")
    print("---------------------------------------------------------------")

    conn_c = conectar(CARREFOUR_DB)
    conn_d = conectar(DISCO_DB)

    if not conn_c and not conn_d:
        print("\n❌ No se pudo conectar a ninguna base de datos.")
        print("💡 Ejecutá primero los scrapers para generar los datos.")
        sys.exit(1)

    carrito_raw = input("Ingrese los productos del carrito, separados por comas: ")
    if not carrito_raw.strip():
        print("⚠️ No ingresó productos. Saliendo.")
        sys.exit(0)

    # Guardamos la entrada en la variable `carrito` como pidió el usuario
    carrito = [t.strip() for t in carrito_raw.split(',') if t.strip()]

    seleccionados = []  # lista de tuplas (store, id, nombre, precio, promo, cantidad)

    # Flujo: elegir tienda primero, luego todos los items en esa tienda
    def elegir_tienda():
        print("\n¿Por cuál tienda empezamos?")
        if conn_c:
            print("  1) Carrefour 🛒")
        if conn_d:
            print("  2) Disco 🛍️")
        while True:
            sel = input("  Ingrese 1 o 2: ").strip()
            if sel == '1' and conn_c:
                return "Carrefour"
            elif sel == '2' and conn_d:
                return "Disco"
            print("  Entrada inválida. Intente de nuevo.")

    tiendas_orden = [elegir_tienda()]
    if conn_c and conn_d:
        otra = "Disco" if tiendas_orden[0] == "Carrefour" else "Carrefour"
        tiendas_orden.append(otra)

    for tienda_actual in tiendas_orden:
        conn_tienda = conn_c if tienda_actual == "Carrefour" else conn_d
        print(f"\n{'=' * 60}")
        print(f"🛒 Buscando productos en {tienda_actual}...")
        print(f"{'=' * 60}")

        for termino in carrito:
            print(f"\n🔎 Buscando: '{termino}' en {tienda_actual}...")
            # Búsqueda estricta primero
            matches = buscar_coincidencias(conn_tienda, termino, strict=True)

            # Fallback: buscar por primera palabra
            if not matches:
                primera = termino.strip().split()[0] if termino.strip() else termino
                if primera and primera.lower() != termino.lower():
                    print(f"  ⚠️ No encontré '{termino}' estrictamente. Mostrando coincidencias para '{primera}':")
                    matches = buscar_coincidencias(conn_tienda, primera, strict=False)

            # Fallback final: búsqueda laxa
            if not matches:
                matches = buscar_coincidencias(conn_tienda, termino, strict=False)

            if not matches:
                print(f"  ⚠️ No se encontró '{termino}' en {tienda_actual}.")
                continue

            # Si sólo hay una coincidencia, seleccionar automáticamente
            if len(matches) == 1:
                row = matches[0]
                print(f"  ✅ Selección automática: {row[1]} — {formatear_precio(row[2])} — {row[3]}")
                cantidad = pedir_cantidad(row[1])
                seleccionados.append((tienda_actual, row[0], row[1], row[2], row[3], cantidad))
                continue

            # Mostrar opciones para elegir
            all_matches = [(tienda_actual, r) for r in matches]
            elegido = elegir_coincidencia(all_matches, termino)
            if elegido:
                _, row = elegido
                cantidad = pedir_cantidad(row[1])
                seleccionados.append((tienda_actual, row[0], row[1], row[2], row[3], cantidad))
            else:
                print(f"  Se omitió '{termino}' en {tienda_actual}.")

    # Validar que haya selecciones
    if not seleccionados:
        print("\n⚠️ No se seleccionaron productos. Fin.")

        # Antes de salir, cerramos conexiones
        if conn_c:
            conn_c.close()
        if conn_d:
            conn_d.close()
        return

    # --- Mostrar totales por tienda ---
    resumen = {}
    for tienda, _id, nombre, precio, promo, cantidad in seleccionados:
        resumen.setdefault(tienda, []).append((nombre, precio, promo, cantidad))

    print("\n" + "=" * 60)
    print("\n💰 ===== Totales por tienda (de tus selecciones) =====")
    for store_name in ["Carrefour", "Disco"]:
        if store_name in resumen:
            items = resumen[store_name]
            subtotal = 0.0
            store_icon = '🛒' if store_name == 'Carrefour' else '🛍️'
            print(f"\n{store_icon} {store_name}:")
            for nombre, precio, promo, cantidad in items:
                precio_float = float(precio)
                total_item, precio_unitario_final = calcular_precio_con_promo(precio_float, promo, cantidad)
                subtotal += total_item
                
                flag = "(PROMO)" if promo and promo.lower() != 'precio regular' else ""
                if cantidad > 1:
                    print(f"  - {nombre} x{cantidad} — {formatear_precio(precio_float)} c/u = {formatear_precio(total_item)} {flag} — {promo}")
                else:
                    print(f"  - {nombre} — {formatear_precio(precio_float)} {flag} — {promo}")
            print(f"  💳 Subtotal {store_name}: {formatear_precio(subtotal)}")
        else:
            store_icon = '🛒' if store_name == 'Carrefour' else '🛍️'
            if (store_name == "Carrefour" and conn_c) or (store_name == "Disco" and conn_d):
                print(f"\n{store_icon} {store_name}: (sin selecciones)")

    # Mostrar recomendación si hay ambas tiendas
    if "Carrefour" in resumen and "Disco" in resumen:
        total_c = sum(calcular_precio_con_promo(float(p), pr, c)[0] for _, p, pr, c in resumen["Carrefour"])
        total_d = sum(calcular_precio_con_promo(float(p), pr, c)[0] for _, p, pr, c in resumen["Disco"])
        
        print("\n" + "=" * 60)
        print("💡 RECOMENDACIÓN:")
        print("=" * 60)
        
        if total_c < total_d:
            ahorro = total_d - total_c
            print(f"✅ Comprá en CARREFOUR 🛒")
            print(f"   Ahorrás: {formatear_precio(ahorro)} ({(ahorro/total_d)*100:.1f}%)")
        elif total_d < total_c:
            ahorro = total_c - total_d
            print(f"✅ Comprá en DISCO 🛍️")
            print(f"   Ahorrás: {formatear_precio(ahorro)} ({(ahorro/total_c)*100:.1f}%)")
        else:
            print("🤝 Mismo precio en ambas tiendas")

    print("\n✅ Fin del análisis.")

    # Cerrar conexiones
    if conn_c:
        conn_c.close()
    if conn_d:
        conn_d.close()

    return


if __name__ == '__main__':
    main()
