import os
from supabase import create_client, Client
from dotenv import load_dotenv
import sys

# Cargar .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

print(f"📁 Cargando .env desde: {env_path}")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

print(f"✅ SUPABASE_URL: {SUPABASE_URL[:30]}...")
print(f"✅ SERVICE_KEY cargada: {SUPABASE_SERVICE_KEY is not None}")
print(f"✅ ANON_KEY cargada: {SUPABASE_ANON_KEY is not None}")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not SUPABASE_ANON_KEY:
    print("❌ ERROR: Faltan variables de entorno")
    sys.exit(1)

# Cliente admin (service_role)
try:
    supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    print("✅ Cliente admin creado correctamente")
except Exception as e:
    print(f"❌ Error creando cliente admin: {e}")
    sys.exit(1)

def get_supabase_admin():
    """Cliente admin para scrapers (bypasea RLS)"""
    return supabase_admin

def get_supabase_anon():
    """Cliente público (respeta RLS)"""
    try:
        return create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    except Exception as e:
        print(f"❌ Error creando cliente anon: {e}")
        raise