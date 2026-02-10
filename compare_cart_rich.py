#!/usr/bin/env python3
"""
Comparador de carritos mejorado con interfaz rica.
Muestra productos con fotos y mejor visualización.
"""

import sqlite3
import os
import sys
import unicodedata
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CARREFOUR_DB = os.path.join(DATA_DIR, 'carrefour.db')
DISCO_DB = os.path.join(DATA_DIR, 'disco.db')


def conectar(db_path):
    """Conecta a la base de datos"""
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(db_path)
        
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
        console.print(f"[red]❌ Error conectando a {db_path}: {e}[/red]")
        return None


def buscar_coincidencias(conn, termino, limit=50, strict=False):
    """Busca coincidencias en la DB"""
    if conn is None:
        return []
    cur = conn.cursor()
    texto = termino.lower().strip()
    if not texto:
        return []

    try:
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
            query = f"SELECT id, nombre, precio_actual as precio, promo_actual as promo, url FROM productos WHERE {where_clauses} ORDER BY nombre LIMIT ?"
            cur.execute(query, params)
            return cur.fetchall()
        else:
            pattern = f"%{normalizar(texto)}%"
            cur.execute("SELECT id, nombre, precio_actual as precio, promo_actual as promo, url FROM productos WHERE unaccent(LOWER(nombre)) LIKE ? ORDER BY nombre LIMIT ?", (pattern, limit))
            return cur.fetchall()
    except Exception:
        # Fallback para DBs viejas
        try:
            if strict:
                words = [w for w in texto.split() if w]
                if not words:
                    return []
                where_clauses = ' AND '.join(['unaccent(LOWER(nombre)) LIKE ?' for _ in words])
                params = [f"%{normalizar(w)}%" for w in words] + [limit]
                query = f"SELECT id, nombre, precio, promo, NULL as url FROM productos WHERE {where_clauses} ORDER BY nombre LIMIT ?"
                cur.execute(query, params)
                return cur.fetchall()
            else:
                pattern = f"%{normalizar(texto)}%"
                cur.execute("SELECT id, nombre, precio, promo, NULL as url FROM productos WHERE unaccent(LOWER(nombre)) LIKE ? ORDER BY nombre LIMIT ?", (pattern, limit))
                return cur.fetchall()
        except Exception:
            return []


def formatear_precio(p):
    """Formatea un precio"""
    try:
        return f"${float(p):,.2f}"
    except Exception:
        return str(p)


def mostrar_producto(nombre, precio, promo, tienda, url=None):
    """Muestra un producto con formato rico"""
    # Icono según tienda
    icono = "🛒" if tienda.lower() == "carrefour" else "🛍️"
    
    # Color según si tiene promo
    tiene_promo = promo and promo.lower() != 'precio regular'
    color_precio = "green" if tiene_promo else "white"
    
    # Crear tabla del producto
    table = Table(show_header=False, box=box.ROUNDED, padding=(0, 1))
    table.add_column("Campo", style="cyan")
    table.add_column("Valor")
    
    table.add_row("Tienda", f"{icono} {tienda}")
    table.add_row("Producto", f"[bold]{nombre}[/bold]")
    table.add_row("Precio", f"[{color_precio}]{formatear_precio(precio)}[/{color_precio}]")
    
    if tiene_promo:
        table.add_row("Promoción", f"[yellow]🏷️  {promo}[/yellow]")
    
    if url:
        # Acortar URL para display
        url_corta = url[:50] + "..." if len(url) > 50 else url
        table.add_row("Link", f"[dim]{url_corta}[/dim]")
    
    return table


def elegir_coincidencia_mejorado(all_matches, termino):
    """Interfaz mejorada para elegir productos"""
    if not all_matches:
        console.print(f"\n[yellow]⚠️  No se encontraron coincidencias para '[bold]{termino}[/bold]'[/yellow]")
        return None
    
    console.print(f"\n[cyan]🔍 Resultados para:[/cyan] [bold]{termino}[/bold]")
    console.print(f"[dim]Encontrados: {len(all_matches)} productos[/dim]\n")
    
    # Mostrar opciones
    table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    table.add_column("#", style="cyan", width=4)
    table.add_column("Tienda", width=12)
    table.add_column("Producto", style="bold")
    table.add_column("Precio", justify="right", width=12)
    table.add_column("Promo", width=20)
    
    for i, (store, row) in enumerate(all_matches[:10], 1):  # Mostrar solo primeros 10
        _id, nombre, precio, promo, url = row
        icono = "🛒" if store.lower() == "carrefour" else "🛍️"
        
        # Acortar nombre si es muy largo
        nombre_corto = nombre[:40] + "..." if len(nombre) > 40 else nombre
        
        # Color según promo
        tiene_promo = promo and promo.lower() != 'precio regular'
        promo_texto = f"[yellow]{promo}[/yellow]" if tiene_promo else "[dim]Sin promo[/dim]"
        
        table.add_row(
            str(i),
            f"{icono} {store}",
            nombre_corto,
            f"[green]{formatear_precio(precio)}[/green]",
            promo_texto
        )
    
    console.print(table)
    
    if len(all_matches) > 10:
        console.print(f"\n[dim]... y {len(all_matches) - 10} más[/dim]")
    
    # Pedir selección
    console.print("\n[cyan]Comandos:[/cyan]")
    console.print("  • [bold]Número[/bold] - Elegir producto")
    console.print("  • [bold]s[/bold] - Saltar este producto")
    console.print("  • [bold]c[/bold] - Filtrar solo Carrefour")
    console.print("  • [bold]d[/bold] - Filtrar solo Disco\n")
    
    while True:
        seleccion = Prompt.ask("[bold]Tu elección[/bold]", default="s")
        
        if seleccion.lower() == 's' or seleccion == '':
            return None
        
        if seleccion.lower() == 'c':
            filtered = [m for m in all_matches if m[0].lower() == 'carrefour']
            return elegir_coincidencia_mejorado(filtered, termino)
        
        if seleccion.lower() == 'd':
            filtered = [m for m in all_matches if m[0].lower() == 'disco']
            return elegir_coincidencia_mejorado(filtered, termino)
        
        if seleccion.isdigit():
            idx = int(seleccion) - 1
            if 0 <= idx < min(len(all_matches), 10):
                return all_matches[idx]
            else:
                console.print("[red]⚠️  Número inválido[/red]")
        else:
            console.print("[red]⚠️  Comando no reconocido[/red]")


def pedir_cantidad(nombre):
    """Pide cantidad con mejor interfaz"""
    while True:
        cantidad = Prompt.ask(
            f"[cyan]¿Cuánto(s)[/cyan] [bold]{nombre}[/bold]",
            default="1"
        )
        
        if cantidad.isdigit() and int(cantidad) > 0:
            return int(cantidad)
        
        console.print("[red]⚠️  Ingresá un número válido[/red]")


def calcular_precio_con_promo(precio_base, promo, cantidad):
    """Calcula precio con promos"""
    precio_base_float = float(precio_base)
    
    if not promo or promo.lower() == 'precio regular':
        return precio_base_float * cantidad, precio_base_float
    
    import re
    match = re.search(r'2DO\s+AL\s+(\d+)%|SEGUNDO\s+AL\s+(\d+)%', promo.upper())
    if match:
        descuento_pct = int(match.group(1) or match.group(2))
        precio_segundo = precio_base_float * (descuento_pct / 100.0)
        
        if cantidad == 1:
            return precio_base_float, precio_base_float
        elif cantidad == 2:
            total = precio_base_float + precio_segundo
            return total, precio_segundo
        else:
            pares = cantidad // 2
            sobrante = cantidad % 2
            total = pares * (precio_base_float + precio_segundo) + sobrante * precio_base_float
            return total, precio_segundo
    
    return precio_base_float * cantidad, precio_base_float


def mostrar_resumen(seleccionados):
    """Muestra resumen final con recomendación"""
    if not seleccionados:
        console.print("\n[yellow]⚠️  No hay productos seleccionados[/yellow]")
        return
    
    # Agrupar por tienda
    por_tienda = {}
    for tienda, _id, nombre, precio, promo, url, cantidad in seleccionados:
        if tienda not in por_tienda:
            por_tienda[tienda] = []
        por_tienda[tienda].append((nombre, precio, promo, cantidad))
    
    # Mostrar cada tienda
    console.print("\n" + "="*60)
    console.print("\n[bold cyan]💰 RESUMEN DE COMPRA[/bold cyan]\n")
    
    totales = {}
    
    for tienda, productos in por_tienda.items():
        icono = "🛒" if tienda.lower() == "carrefour" else "🛍️"
        
        # Tabla por tienda
        table = Table(
            title=f"{icono} {tienda}",
            show_header=True,
            header_style="bold magenta",
            box=box.ROUNDED
        )
        table.add_column("Producto", style="bold")
        table.add_column("Cant.", justify="center", width=6)
        table.add_column("Precio Unit.", justify="right")
        table.add_column("Total", justify="right", style="green")
        table.add_column("Promo", width=15)
        
        subtotal = 0.0
        
        for nombre, precio, promo, cantidad in productos:
            precio_float = float(precio)
            total_item, _ = calcular_precio_con_promo(precio_float, promo, cantidad)
            subtotal += total_item
            
            # Acortar nombre
            nombre_corto = nombre[:30] + "..." if len(nombre) > 30 else nombre
            
            # Promo visual
            tiene_promo = promo and promo.lower() != 'precio regular'
            promo_texto = f"[yellow]{promo[:15]}...[/yellow]" if tiene_promo and len(promo) > 15 else (f"[yellow]{promo}[/yellow]" if tiene_promo else "[dim]-[/dim]")
            
            table.add_row(
                nombre_corto,
                str(cantidad),
                formatear_precio(precio_float),
                f"[bold]{formatear_precio(total_item)}[/bold]",
                promo_texto
            )
        
        # Total por tienda
        table.add_row(
            "",
            "",
            "",
            f"[bold green]{formatear_precio(subtotal)}[/bold green]",
            "",
            style="bold"
        )
        
        console.print(table)
        console.print()
        
        totales[tienda] = subtotal
    
    # Recomendación
    if len(totales) > 1:
        console.print("="*60)
        console.print("\n[bold cyan]💡 RECOMENDACIÓN[/bold cyan]\n")
        
        tienda_ganadora = min(totales, key=totales.get)
        tienda_perdedora = max(totales, key=totales.get)
        
        ahorro = totales[tienda_perdedora] - totales[tienda_ganadora]
        porcentaje = (ahorro / totales[tienda_perdedora]) * 100
        
        icono_ganador = "🛒" if tienda_ganadora.lower() == "carrefour" else "🛍️"
        
        panel = Panel(
            f"[bold green]Comprá en {icono_ganador} {tienda_ganadora.upper()}[/bold green]\n\n"
            f"💰 Ahorrás: [bold]{formatear_precio(ahorro)}[/bold] ([cyan]{porcentaje:.1f}%[/cyan])",
            style="green",
            box=box.DOUBLE
        )
        console.print(panel)
    
    console.print("\n" + "="*60 + "\n")


def main():
    """Función principal con interfaz mejorada"""
    console.clear()
    
    # Banner
    console.print(Panel.fit(
        "[bold cyan]🛒 COMPARADOR DE PRECIOS[/bold cyan]\n"
        "[dim]Compará precios entre Carrefour y Disco[/dim]",
        border_style="cyan"
    ))
    
    # Conectar a DBs
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Conectando a bases de datos...", total=None)
        conn_c = conectar(CARREFOUR_DB)
        conn_d = conectar(DISCO_DB)
        progress.update(task, completed=True)
    
    if not conn_c and not conn_d:
        console.print("\n[red]❌ No se pudo conectar a ninguna base de datos[/red]")
        console.print("[yellow]💡 Ejecutá primero los scrapers o descargá las DBs[/yellow]\n")
        sys.exit(1)
    
    # Verificar disponibilidad
    console.print()
    if conn_c:
        console.print("[green]✅ Carrefour: Disponible[/green]")
    else:
        console.print("[red]❌ Carrefour: No disponible[/red]")
    
    if conn_d:
        console.print("[green]✅ Disco: Disponible[/green]")
    else:
        console.print("[red]❌ Disco: No disponible[/red]")
    
    console.print()
    
    # Pedir productos
    carrito_raw = Prompt.ask(
        "[bold cyan]Ingresá los productos[/bold cyan] [dim](separados por comas)[/dim]"
    )
    
    if not carrito_raw.strip():
        console.print("\n[yellow]⚠️  No ingresaste productos[/yellow]\n")
        sys.exit(0)
    
    carrito = [t.strip() for t in carrito_raw.split(',') if t.strip()]
    
    seleccionados = []
    
    # Elegir tienda inicial
    if conn_c and conn_d:
        console.print("\n[cyan]¿Por cuál tienda empezamos?[/cyan]")
        tienda_inicial = Prompt.ask(
            "Elegí una tienda",
            choices=["carrefour", "disco"],
            default="carrefour"
        )
        tiendas_orden = [tienda_inicial.capitalize(), "Disco" if tienda_inicial == "carrefour" else "Carrefour"]
    elif conn_c:
        tiendas_orden = ["Carrefour"]
    else:
        tiendas_orden = ["Disco"]
    
    # Buscar productos
    for tienda_actual in tiendas_orden:
        conn_tienda = conn_c if tienda_actual == "Carrefour" else conn_d
        
        if not conn_tienda:
            continue
        
        console.print(f"\n{'='*60}")
        console.print(f"\n[bold cyan]🔍 Buscando en {tienda_actual}...[/bold cyan]\n")
        
        for termino in carrito:
            # Búsqueda con spinner
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"[cyan]Buscando '{termino}'...", total=None)
                
                matches = buscar_coincidencias(conn_tienda, termino, strict=True)
                
                if not matches:
                    primera = termino.strip().split()[0] if termino.strip() else termino
                    if primera and primera.lower() != termino.lower():
                        matches = buscar_coincidencias(conn_tienda, primera, strict=False)
                
                if not matches:
                    matches = buscar_coincidencias(conn_tienda, termino, strict=False)
                
                progress.update(task, completed=True)
            
            if not matches:
                console.print(f"[yellow]⚠️  No se encontró '{termino}' en {tienda_actual}[/yellow]")
                continue
            
            # Si hay una sola coincidencia, selección automática
            if len(matches) == 1:
                row = matches[0]
                _id, nombre, precio, promo, url = row
                console.print(f"\n[green]✅ Selección automática:[/green] [bold]{nombre}[/bold]")
                console.print(f"   Precio: [green]{formatear_precio(precio)}[/green]")
                if promo and promo.lower() != 'precio regular':
                    console.print(f"   Promo: [yellow]{promo}[/yellow]")
                
                cantidad = pedir_cantidad(nombre)
                seleccionados.append((tienda_actual, _id, nombre, precio, promo, url, cantidad))
                continue
            
            # Múltiples coincidencias
            all_matches = [(tienda_actual, r) for r in matches]
            elegido = elegir_coincidencia_mejorado(all_matches, termino)
            
            if elegido:
                _, row = elegido
                _id, nombre, precio, promo, url = row
                cantidad = pedir_cantidad(nombre)
                seleccionados.append((tienda_actual, _id, nombre, precio, promo, url, cantidad))
            else:
                console.print(f"[dim]⏭️  Producto '{termino}' omitido[/dim]")
    
    # Mostrar resumen
    mostrar_resumen(seleccionados)
    
    # Cerrar conexiones
    if conn_c:
        conn_c.close()
    if conn_d:
        conn_d.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 ¡Chau![/yellow]\n")
        sys.exit(0)
