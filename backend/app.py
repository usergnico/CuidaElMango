from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from database import get_supabase_admin
from matching import calcular_match_score, encontrar_mejores_matches

# Inicializar FastAPI
app = FastAPI(title="CuidaElMango API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cliente Supabase
supabase = get_supabase_admin()


# ============================================
# MODELOS
# ============================================

class ProductoComparacion(BaseModel):
    id: int
    nombre: str
    tienda: str
    marca: Optional[str] = None
    peso: Optional[float] = None
    peso_unidad: Optional[str] = None
    categoria: Optional[str] = None
    variante: Optional[str] = None
    precio: float


class RequestComparacion(BaseModel):
    productos: List[ProductoComparacion]


# ============================================
# ENDPOINTS BÁSICOS
# ============================================

@app.get("/")
async def root():
    return {
        "message": "CuidaElMango API",
        "version": "2.0",
        "endpoints": [
            "/productos/buscar",
            "/comparar-inteligente",
            "/equivalencias"
        ]
    }


@app.get("/test-db")
async def test_db():
    try:
        result = supabase.table("productos").select("count").execute()
        return {"status": "ok", "message": "Conexión a Supabase exitosa"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ============================================
# ENDPOINTS DE BÚSQUEDA
# ============================================

@app.get("/productos/buscar")
async def buscar_productos(query: str, tienda: Optional[str] = None, limit: int = 50):
    """
    Busca productos por nombre (con normalización de acentos)
    """
    try:
        busqueda_query = supabase.table("productos").select("*")
        
        # Filtrar por tienda si se especifica
        if tienda:
            busqueda_query = busqueda_query.eq("tienda", tienda)
        
        # Buscar por nombre normalizado
        busqueda_query = busqueda_query.ilike("nombre_normalizado", f"%{query}%")
        busqueda_query = busqueda_query.limit(limit)
        
        result = busqueda_query.execute()
        
        return {
            "query": query,
            "count": len(result.data) if result.data else 0,
            "productos": result.data or []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINTS DE COMPARACIÓN INTELIGENTE
# ============================================

@app.post("/comparar-inteligente")
async def comparar_inteligente(request: RequestComparacion):
    """
    Compara productos usando matching inteligente
    
    Para cada producto seleccionado:
    1. Busca candidatos en la tienda opuesta
    2. Calcula score de matching
    3. Retorna el mejor match + alternativas
    """
    
    try:
        resultados = {
            "Carrefour": [],
            "Disco": [],
            "metadata": {
                "total_productos": len(request.productos),
                "matches_encontrados": 0,
                "matches_alta_confianza": 0,
                "productos_sin_match": 0
            }
        }
        
        for producto in request.productos:
            tienda_origen = producto.tienda
            tienda_opuesta = "Disco" if tienda_origen == "Carrefour" else "Carrefour"
            
            # Agregar producto origen a su tienda
            resultados[tienda_origen].append({
                **producto.dict(),
                "es_origen": True
            })
            
            # Buscar candidatos en tienda opuesta
            candidatos = await buscar_candidatos(producto, tienda_opuesta)
            
            if not candidatos:
                # No hay candidatos
                resultados[tienda_opuesta].append({
                    "id": f"missing-{producto.id}",
                    "nombre": "❌ Producto no disponible",
                    "tienda": tienda_opuesta,
                    "precio": 0,
                    "no_disponible": True,
                    "producto_origen_id": producto.id
                })
                resultados["metadata"]["productos_sin_match"] += 1
                continue
            
            # Calcular scores para candidatos
            matches = encontrar_mejores_matches(producto.dict(), candidatos, top_n=5)
            
            mejor_match = matches[0]
            
            # Agregar mejor match
            resultados[tienda_opuesta].append({
                **mejor_match,
                "es_match_automatico": True,
                "producto_origen_id": producto.id,
                "alternativas": matches[1:4] if len(matches) > 1 else []
            })
            
            resultados["metadata"]["matches_encontrados"] += 1
            
            if mejor_match["match_score"] >= 80:
                resultados["metadata"]["matches_alta_confianza"] += 1
        
        # Calcular totales
        resultados["totales"] = {
            "Carrefour": sum(
                p.get("precio", 0) 
                for p in resultados["Carrefour"] 
                if not p.get("no_disponible")
            ),
            "Disco": sum(
                p.get("precio", 0) 
                for p in resultados["Disco"] 
                if not p.get("no_disponible")
            )
        }
        
        # Determinar mejor opción
        if resultados["totales"]["Carrefour"] > 0 and resultados["totales"]["Disco"] > 0:
            if resultados["totales"]["Carrefour"] < resultados["totales"]["Disco"]:
                mejor_opcion = "Carrefour"
                ahorro = resultados["totales"]["Disco"] - resultados["totales"]["Carrefour"]
            else:
                mejor_opcion = "Disco"
                ahorro = resultados["totales"]["Carrefour"] - resultados["totales"]["Disco"]
            
            resultados["recomendacion"] = {
                "tienda": mejor_opcion,
                "ahorro": round(ahorro, 2),
                "porcentaje": round(
                    (ahorro / max(resultados["totales"]["Carrefour"], resultados["totales"]["Disco"])) * 100, 
                    1
                )
            }
        
        return resultados
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def buscar_candidatos(producto: ProductoComparacion, tienda: str):
    """
    Busca productos candidatos para matching
    
    Estrategia:
    1. Marca + categoría + peso similar (±30%)
    2. Fallback: Marca + categoría
    3. Fallback: Solo marca
    4. Fallback: Categoría + palabra clave
    """
    
    candidatos = []
    
    # Estrategia 1: Marca + categoría + peso
    if producto.marca and producto.categoria and producto.peso:
        query = supabase.table("productos").select("*")
        query = query.eq("tienda", tienda)
        query = query.eq("marca", producto.marca)
        query = query.eq("categoria", producto.categoria)
        
        # Peso ±30%
        peso_min = producto.peso * 0.7
        peso_max = producto.peso * 1.3
        query = query.gte("peso", peso_min)
        query = query.lte("peso", peso_max)
        
        result = query.limit(10).execute()
        
        if result.data:
            candidatos = result.data
    
    # Estrategia 2: Marca + categoría (sin filtro de peso)
    if not candidatos and producto.marca and producto.categoria:
        result = supabase.table("productos").select("*") \
            .eq("tienda", tienda) \
            .eq("marca", producto.marca) \
            .eq("categoria", producto.categoria) \
            .limit(10) \
            .execute()
        
        if result.data:
            candidatos = result.data
    
    # Estrategia 3: Solo marca
    if not candidatos and producto.marca:
        result = supabase.table("productos").select("*") \
            .eq("tienda", tienda) \
            .eq("marca", producto.marca) \
            .limit(10) \
            .execute()
        
        if result.data:
            candidatos = result.data
    
    # Estrategia 4: Categoría + nombre normalizado
    if not candidatos and producto.categoria:
        # Extraer palabra clave del nombre
        palabras = producto.nombre.lower().split()
        palabra_clave = next((p for p in palabras if len(p) > 4), palabras[0] if palabras else "")
        
        if palabra_clave:
            result = supabase.table("productos").select("*") \
                .eq("tienda", tienda) \
                .eq("categoria", producto.categoria) \
                .ilike("nombre_normalizado", f"%{palabra_clave}%") \
                .limit(10) \
                .execute()
            
            if result.data:
                candidatos = result.data
    
    return candidatos


# ============================================
# ENDPOINTS DE EQUIVALENCIAS
# ============================================

@app.post("/equivalencias")
async def crear_equivalencia(producto_a_id: int, producto_b_id: int):
    """
    Guarda una equivalencia manual entre dos productos
    (cuando el usuario corrige un match automático)
    """
    
    try:
        result = supabase.table("equivalencias").upsert({
            "producto_a_id": producto_a_id,
            "producto_b_id": producto_b_id,
            "confianza": 100,
            "corregido_por_usuario": True
        }).execute()
        
        return {"success": True, "data": result.data}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/equivalencias/{producto_id}")
async def buscar_equivalencia(producto_id: int):
    """
    Busca si existe una equivalencia guardada para un producto
    """
    
    try:
        # Buscar en ambas direcciones
        result_a = supabase.table("equivalencias").select("*, productos!producto_b_id(*)") \
            .eq("producto_a_id", producto_id) \
            .execute()
        
        result_b = supabase.table("equivalencias").select("*, productos!producto_a_id(*)") \
            .eq("producto_b_id", producto_id) \
            .execute()
        
        equivalencias = result_a.data + result_b.data
        
        return {
            "encontrado": len(equivalencias) > 0,
            "equivalencias": equivalencias
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# EJECUTAR
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
