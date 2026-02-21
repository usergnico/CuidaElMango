import { useState } from 'react'
import { supabase } from './config/supabase'
import { Search, Loader2, AlertCircle, X } from 'lucide-react'
import './App.css'

function App() {
  const [busqueda, setBusqueda] = useState('')
  const [loading, setLoading] = useState(false)
  const [resultados, setResultados] = useState(null)
  const [alertas, setAlertas] = useState([])

  const buscarProductosInteligente = async (e) => {
    e.preventDefault()
    
    if (!busqueda.trim()) return

    setLoading(true)
    setAlertas([])
    
    try {
      const productosBuscados = busqueda
        .split(',')
        .map(p => p.trim())
        .filter(p => p.length > 0)

      const carritosArmados = {
        Carrefour: [],
        Disco: []
      }

      const nuevasAlertas = []

      for (const productoBuscado of productosBuscados) {
        // Buscar en Carrefour
        const { data: carrefourResults } = await supabase
          .from('productos')
          .select('*')
          .eq('tienda', 'Carrefour')
          .ilike('nombre', `%${productoBuscado}%`)
          .order('precio', { ascending: true })
          .limit(1)

        // Buscar en Disco
        const { data: discoResults } = await supabase
          .from('productos')
          .select('*')
          .eq('tienda', 'Disco')
          .ilike('nombre', `%${productoBuscado}%`)
          .order('precio', { ascending: true })
          .limit(1)

        if (carrefourResults && carrefourResults.length > 0) {
          carritosArmados.Carrefour.push(carrefourResults[0])
        } else {
          nuevasAlertas.push(`⚠️ "${productoBuscado}" no encontrado en Carrefour`)
        }

        if (discoResults && discoResults.length > 0) {
          carritosArmados.Disco.push(discoResults[0])
        } else {
          nuevasAlertas.push(`⚠️ "${productoBuscado}" no encontrado en Disco`)
        }
      }

      setResultados(carritosArmados)
      setAlertas(nuevasAlertas)

    } catch (error) {
      console.error('Error:', error)
      setAlertas(['❌ Error al buscar productos'])
    } finally {
      setLoading(false)
    }
  }

  const limpiar = () => {
    setBusqueda('')
    setResultados(null)
    setAlertas([])
  }

  const calcularTotal = (productos) => {
    return productos.reduce((sum, p) => sum + parseFloat(p.precio), 0)
  }

  const totalCarrefour = resultados ? calcularTotal(resultados.Carrefour) : 0
  const totalDisco = resultados ? calcularTotal(resultados.Disco) : 0
  
  const mejorOpcion = totalCarrefour > 0 && totalDisco > 0
    ? totalCarrefour < totalDisco ? 'Carrefour' : 'Disco'
    : null
  
  const ahorro = mejorOpcion ? Math.abs(totalCarrefour - totalDisco) : 0
  const porcentajeAhorro = mejorOpcion 
    ? ((ahorro / Math.max(totalCarrefour, totalDisco)) * 100).toFixed(1)
    : 0

  return (
    <div className="app">
      {/* Navbar */}
      <nav className="navbar">
        <div className="container">
          <a href="/" className="logo">
            🥭 CuidaElMango
          </a>
          <a 
            href="https://github.com/usergnico/CuidaElMango" 
            target="_blank" 
            rel="noopener noreferrer"
            className="github-link"
          >
            GitHub
          </a>
        </div>
      </nav>

      {/* Main Content */}
      <main className="main">
        <div className="container">
          {/* Hero */}
          <div className="hero">
            <h1>🥭 CuidaElMango</h1>
            <p>Ingresá los productos que quieras comparar</p>
          </div>

          {/* Buscador */}
          <div className="search-section">
            <div className="search-card">
              <h2>Comparar Precios</h2>
              <p className="subtitle">Escribí los productos separados por comas</p>

              <form onSubmit={buscarProductosInteligente}>
                <div className="input-wrapper">
                  <input
                    type="text"
                    value={busqueda}
                    onChange={(e) => setBusqueda(e.target.value)}
                    placeholder="Ej: arroz, aceite 1.5L, atún, fideos"
                    className="search-input"
                    disabled={loading}
                  />
                  <p className="hint">
                    💡 Tip: Sé específico para mejores resultados
                  </p>
                </div>

                <div className="button-group">
                  <button 
                    type="submit" 
                    className="btn btn-primary" 
                    disabled={loading || !busqueda.trim()}
                  >
                    {loading ? (
                      <>
                        <Loader2 className="spin" size={20} />
                        Buscando...
                      </>
                    ) : (
                      <>
                        <Search size={20} />
                        Comparar Precios
                      </>
                    )}
                  </button>

                  {(busqueda || resultados) && (
                    <button 
                      type="button" 
                      className="btn btn-secondary"
                      onClick={limpiar}
                    >
                      <X size={20} />
                      Limpiar
                    </button>
                  )}
                </div>
              </form>
            </div>

            {/* Alertas */}
            {alertas.length > 0 && (
              <div className="alerts">
                {alertas.map((alerta, idx) => (
                  <div key={idx} className="alert">
                    <AlertCircle size={20} />
                    <span>{alerta}</span>
                  </div>
                ))}
              </div>
            )}

            {/* Resultados */}
            {resultados && (
              <div className="results">
                <div className="results-header">
                  <h2>Comparación</h2>
                  <button className="btn-clear" onClick={limpiar}>
                    <X size={18} />
                    Limpiar
                  </button>
                </div>

                {/* Recomendación */}
                {mejorOpcion && ahorro > 0 && (
                  <div className="recommendation">
                    <h3>💡 Los mejores precios se encuentran en {mejorOpcion}</h3>
                    <p className="savings">
                      Ahorrás ${ahorro.toFixed(2)} ({porcentajeAhorro}%)
                    </p>
                  </div>
                )}

                {/* Comparación */}
                <div className="comparison">
                  {/* Carrefour */}
                  <div className="store-card">
                    <div className="store-header">
                      <span className="store-icon">🛒</span>
                      <h3>Carrefour</h3>
                    </div>

                    {resultados.Carrefour.length > 0 ? (
                      <>
                        <div className="products">
                          {resultados.Carrefour.map((producto) => (
                            <div key={producto.id} className="product">
                              <div className="product-name">{producto.nombre}</div>
                              <div className="product-price">
                                ${parseFloat(producto.precio).toFixed(2)}
                              </div>
                              {producto.promo && producto.promo !== 'Precio Regular' && (
                                <div className="product-promo">
                                  🏷️ {producto.promo}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>

                        <div className="store-total">
                          <span>Total:</span>
                          <span>${totalCarrefour.toFixed(2)}</span>
                        </div>
                      </>
                    ) : (
                      <div className="empty">
                        <p>No se encontraron productos</p>
                      </div>
                    )}
                  </div>

                  {/* Disco */}
                  <div className="store-card">
                    <div className="store-header">
                      <span className="store-icon">🛍️</span>
                      <h3>Disco</h3>
                    </div>

                    {resultados.Disco.length > 0 ? (
                      <>
                        <div className="products">
                          {resultados.Disco.map((producto) => (
                            <div key={producto.id} className="product">
                              <div className="product-name">{producto.nombre}</div>
                              <div className="product-price">
                                ${parseFloat(producto.precio).toFixed(2)}
                              </div>
                              {producto.promo && producto.promo !== 'Precio Regular' && (
                                <div className="product-promo">
                                  🏷️ {producto.promo}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>

                        <div className="store-total">
                          <span>Total:</span>
                          <span>${totalDisco.toFixed(2)}</span>
                        </div>
                      </>
                    ) : (
                      <div className="empty">
                        <p>No se encontraron productos</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
