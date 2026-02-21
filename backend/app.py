from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import os
from dotenv import load_dotenv

# Cargar .env
load_dotenv()

app = FastAPI(title="CuidaElMango API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En desarrollo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    """Endpoint raíz"""
    return {
        "status": "online",
        "service": "CuidaElMango API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health():
    """Health check"""
    return {"status": "healthy"}

# Importar database solo DESPUÉS de cargar .env
try:
    from database import get_supabase_anon
    
    @app.get("/test-db")
    def test_db():
        """Test de conexión a Supabase"""
        try:
            supabase = get_supabase_anon()
            response = supabase.table("productos").select("count").execute()
            return {"status": "ok", "message": "Conexión exitosa"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    @app.get("/productos/buscar")
    def buscar_productos(query: str, limit: int = 20):
        """Busca productos"""
        try:
            supabase = get_supabase_anon()
            
            response = supabase.table("productos") \
                .select("*") \
                .ilike("nombre", f"%{query}%") \
                .limit(limit) \
                .execute()
            
            return {
                "success": True,
                "count": len(response.data),
                "productos": response.data
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

except Exception as e:
    print(f"⚠️  No se pudo importar database: {e}")
    print("La API funcionará en modo limitado")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)