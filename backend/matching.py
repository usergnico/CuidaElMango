"""
Sistema de Matching Inteligente para CuidaElMango
Calcula similitud entre productos de diferentes supermercados
"""

from difflib import SequenceMatcher


def calcular_match_score(producto_a, producto_b):
    """
    Calcula score de similitud entre dos productos (0-100)
    
    Criterios:
    - 100: Productos idénticos
    - 85-99: Muy alta probabilidad de ser el mismo
    - 70-84: Alta probabilidad (similar)
    - 50-69: Media probabilidad (requiere revisión)
    - < 50: Baja probabilidad (diferentes)
    
    Args:
        producto_a (dict): Primer producto
        producto_b (dict): Segundo producto
        
    Returns:
        int: Score de 0 a 100
    """
    
    score = 0
    detalles = []
    
    # ============================================
    # 1. MARCA (Peso: 35 puntos)
    # ============================================
    marca_a = producto_a.get('marca')
    marca_b = producto_b.get('marca')
    
    if marca_a and marca_b:
        if marca_a == marca_b:
            score += 35
            detalles.append(f"✓ Marca idéntica: {marca_a}")
        else:
            similitud_marca = similar_strings(marca_a, marca_b)
            if similitud_marca > 0.8:
                score += 25
                detalles.append(f"~ Marca similar: {marca_a} vs {marca_b} ({similitud_marca:.2f})")
            else:
                detalles.append(f"✗ Marca diferente: {marca_a} vs {marca_b}")
    elif not marca_a and not marca_b:
        # Ambos sin marca detectada
        score += 10
        detalles.append("? Sin marca detectada en ambos")
    else:
        detalles.append(f"✗ Solo uno tiene marca: {marca_a or marca_b}")
    
    # ============================================
    # 2. CATEGORÍA (Peso: 20 puntos)
    # ============================================
    categoria_a = producto_a.get('categoria')
    categoria_b = producto_b.get('categoria')
    
    if categoria_a and categoria_b:
        if categoria_a == categoria_b:
            score += 20
            detalles.append(f"✓ Misma categoría: {categoria_a}")
        else:
            detalles.append(f"✗ Categoría diferente: {categoria_a} vs {categoria_b}")
    
    # ============================================
    # 3. PESO/VOLUMEN (Peso: 30 puntos)
    # ============================================
    peso_a = producto_a.get('peso')
    peso_b = producto_b.get('peso')
    unidad_a = producto_a.get('peso_unidad')
    unidad_b = producto_b.get('peso_unidad')
    
    if peso_a and peso_b and unidad_a and unidad_b:
        # Normalizar a misma unidad
        peso_a_norm = normalizar_peso(peso_a, unidad_a)
        peso_b_norm = normalizar_peso(peso_b, unidad_b)
        
        if peso_a_norm > 0 and peso_b_norm > 0:
            diferencia_pct = abs(peso_a_norm - peso_b_norm) / max(peso_a_norm, peso_b_norm)
            
            if diferencia_pct == 0:
                score += 30
                detalles.append(f"✓ Peso idéntico: {peso_a}{unidad_a}")
            elif diferencia_pct < 0.05:  # 5% diferencia
                score += 25
                detalles.append(f"✓ Peso muy similar: {peso_a}{unidad_a} vs {peso_b}{unidad_b} (Δ{diferencia_pct*100:.1f}%)")
            elif diferencia_pct < 0.10:  # 10% diferencia
                score += 20
                detalles.append(f"~ Peso similar: {peso_a}{unidad_a} vs {peso_b}{unidad_b} (Δ{diferencia_pct*100:.1f}%)")
            elif diferencia_pct < 0.20:  # 20% diferencia
                score += 15
                detalles.append(f"~ Peso aceptable: {peso_a}{unidad_a} vs {peso_b}{unidad_b} (Δ{diferencia_pct*100:.1f}%)")
            elif diferencia_pct < 0.50:  # 50% diferencia
                score += 5
                detalles.append(f"⚠ Peso diferente: {peso_a}{unidad_a} vs {peso_b}{unidad_b} (Δ{diferencia_pct*100:.1f}%)")
            else:
                detalles.append(f"✗ Peso muy diferente: {peso_a}{unidad_a} vs {peso_b}{unidad_b}")
    elif not peso_a and not peso_b:
        score += 10
        detalles.append("? Sin peso en ambos")
    else:
        detalles.append(f"✗ Solo uno tiene peso: {peso_a}{unidad_a} o {peso_b}{unidad_b}")
    
    # ============================================
    # 4. VARIANTE (Peso: 10 puntos + penalización)
    # ============================================
    variante_a = producto_a.get('variante')
    variante_b = producto_b.get('variante')
    
    if variante_a and variante_b:
        if variante_a == variante_b:
            score += 10
            detalles.append(f"✓ Misma variante: {variante_a}")
        else:
            score -= 20  # PENALIZACIÓN FUERTE
            detalles.append(f"✗✗ Variante diferente: {variante_a} vs {variante_b}")
    elif not variante_a and not variante_b:
        score += 10
        detalles.append("✓ Sin variante en ambos")
    else:
        score -= 10  # Penalización media
        detalles.append(f"⚠ Solo uno tiene variante: {variante_a or variante_b}")
    
    # ============================================
    # 5. NOMBRE LIMPIO (Peso: 10 puntos)
    # ============================================
    nombre_limpio_a = producto_a.get('nombre_limpio', '')
    nombre_limpio_b = producto_b.get('nombre_limpio', '')
    
    if nombre_limpio_a and nombre_limpio_b:
        similitud = similar_strings(nombre_limpio_a, nombre_limpio_b)
        puntos_nombre = int(similitud * 10)
        score += puntos_nombre
        
        if similitud > 0.7:
            detalles.append(f"✓ Nombres similares: {similitud:.2f}")
        else:
            detalles.append(f"~ Nombres diferentes: {similitud:.2f}")
    
    # ============================================
    # 6. NORMALIZAR SCORE (0-100)
    # ============================================
    score = max(0, min(100, score))
    
    return {
        'score': score,
        'nivel': get_nivel_confianza(score),
        'detalles': detalles
    }


def normalizar_peso(peso, unidad):
    """
    Normaliza peso/volumen a unidad base
    Peso → gramos
    Volumen → mililitros
    
    Args:
        peso (float): Cantidad
        unidad (str): Unidad (kg, g, l, ml, etc)
        
    Returns:
        float: Peso normalizado
    """
    if not peso or not unidad:
        return 0
    
    unidad = unidad.lower()
    
    # Peso
    if unidad in ['kg']:
        return peso * 1000
    elif unidad in ['g', 'gr', 'grs']:
        return peso
    
    # Volumen
    elif unidad in ['l', 'lt', 'lts']:
        return peso * 1000
    elif unidad in ['ml', 'cc']:
        return peso
    
    return peso


def similar_strings(s1, s2):
    """
    Calcula similitud entre dos strings usando SequenceMatcher
    
    Args:
        s1 (str): Primer string
        s2 (str): Segundo string
        
    Returns:
        float: Similitud de 0 a 1
    """
    if not s1 or not s2:
        return 0
    
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def get_nivel_confianza(score):
    """
    Convierte score numérico en nivel de confianza
    
    Args:
        score (int): Score de 0 a 100
        
    Returns:
        str: Nivel de confianza
    """
    if score >= 90:
        return "MUY_ALTA"
    elif score >= 80:
        return "ALTA"
    elif score >= 70:
        return "MEDIA_ALTA"
    elif score >= 60:
        return "MEDIA"
    elif score >= 50:
        return "MEDIA_BAJA"
    else:
        return "BAJA"


def encontrar_mejores_matches(producto_origen, candidatos, top_n=5):
    """
    Encuentra los mejores matches de una lista de candidatos
    
    Args:
        producto_origen (dict): Producto a comparar
        candidatos (list): Lista de productos candidatos
        top_n (int): Cantidad de mejores matches a retornar
        
    Returns:
        list: Lista de candidatos con scores, ordenada de mayor a menor
    """
    matches_con_score = []
    
    for candidato in candidatos:
        match_result = calcular_match_score(producto_origen, candidato)
        
        matches_con_score.append({
            **candidato,
            'match_score': match_result['score'],
            'match_nivel': match_result['nivel'],
            'match_detalles': match_result['detalles']
        })
    
    # Ordenar por score descendente
    matches_con_score.sort(key=lambda x: x['match_score'], reverse=True)
    
    return matches_con_score[:top_n]


# ============================================
# TESTS
# ============================================
if __name__ == "__main__":
    print("=" * 80)
    print("TESTS DE MATCHING")
    print("=" * 80)
    
    # Test 1: Productos idénticos
    print("\n1. PRODUCTOS IDÉNTICOS:")
    producto_a = {
        'nombre': 'Atún al natural La Campagnola 170g',
        'marca': 'campagnola',
        'peso': 170,
        'peso_unidad': 'g',
        'categoria': 'almacen',
        'variante': None,
        'nombre_limpio': 'atun natural'
    }
    
    producto_b = {
        'nombre': 'Atún La Campagnola al natural 170 g',
        'marca': 'campagnola',
        'peso': 170,
        'peso_unidad': 'g',
        'categoria': 'almacen',
        'variante': None,
        'nombre_limpio': 'atun natural'
    }
    
    resultado = calcular_match_score(producto_a, producto_b)
    print(f"Score: {resultado['score']} ({resultado['nivel']})")
    for detalle in resultado['detalles']:
        print(f"  {detalle}")
    
    # Test 2: Productos similares (peso ligeramente diferente)
    print("\n2. PRODUCTOS SIMILARES (peso diferente):")
    producto_c = {
        'nombre': 'Oreo Clásica 117g',
        'marca': 'oreo',
        'peso': 117,
        'peso_unidad': 'g',
        'categoria': 'almacen',
        'variante': 'clasica',
        'nombre_limpio': 'oreo'
    }
    
    producto_d = {
        'nombre': 'Oreo Original 120g',
        'marca': 'oreo',
        'peso': 120,
        'peso_unidad': 'g',
        'categoria': 'almacen',
        'variante': 'original',
        'nombre_limpio': 'oreo'
    }
    
    resultado = calcular_match_score(producto_c, producto_d)
    print(f"Score: {resultado['score']} ({resultado['nivel']})")
    for detalle in resultado['detalles']:
        print(f"  {detalle}")
    
    # Test 3: Productos diferentes (variante diferente)
    print("\n3. PRODUCTOS DIFERENTES (variante):")
    producto_e = {
        'nombre': 'Oreo Clásica 300g',
        'marca': 'oreo',
        'peso': 300,
        'peso_unidad': 'g',
        'categoria': 'almacen',
        'variante': 'clasica',
        'nombre_limpio': 'oreo'
    }
    
    producto_f = {
        'nombre': 'Oreo Mini 125g',
        'marca': 'oreo',
        'peso': 125,
        'peso_unidad': 'g',
        'categoria': 'almacen',
        'variante': 'mini',
        'nombre_limpio': 'oreo'
    }
    
    resultado = calcular_match_score(producto_e, producto_f)
    print(f"Score: {resultado['score']} ({resultado['nivel']})")
    for detalle in resultado['detalles']:
        print(f"  {detalle}")
    
    # Test 4: Productos completamente diferentes
    print("\n4. PRODUCTOS COMPLETAMENTE DIFERENTES:")
    producto_g = {
        'nombre': 'Atún La Campagnola 170g',
        'marca': 'campagnola',
        'peso': 170,
        'peso_unidad': 'g',
        'categoria': 'almacen',
        'variante': None,
        'nombre_limpio': 'atun'
    }
    
    producto_h = {
        'nombre': 'Jabón Palmolive 85g',
        'marca': 'palmolive',
        'peso': 85,
        'peso_unidad': 'g',
        'categoria': 'limpieza',
        'variante': None,
        'nombre_limpio': 'jabon'
    }
    
    resultado = calcular_match_score(producto_g, producto_h)
    print(f"Score: {resultado['score']} ({resultado['nivel']})")
    for detalle in resultado['detalles']:
        print(f"  {detalle}")
