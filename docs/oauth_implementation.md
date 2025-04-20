# Implementación de Autenticación OAuth para GENIA MCP

Este documento detalla la implementación de autenticación OAuth para el proyecto GENIA MCP, permitiendo a los usuarios iniciar sesión con Google y Facebook.

## Configuración de Proveedores OAuth

### Google OAuth

1. **Configuración en Google Cloud Console**:
   - Crear un proyecto en [Google Cloud Console](https://console.cloud.google.com/)
   - Configurar la pantalla de consentimiento OAuth
   - Crear credenciales OAuth 2.0 con los siguientes datos:
     - Tipo: Aplicación web
     - Nombre: GENIA MCP
     - URIs de redirección autorizados:
       - `https://[TU-PROYECTO].supabase.co/auth/v1/callback`
       - `http://localhost:5173/auth/callback/google` (para desarrollo)
       - `https://genia-frontendmpc.vercel.app/auth/callback/google` (para producción)
   - Obtener Client ID y Client Secret

2. **Configuración en Supabase**:
   - En el dashboard de Supabase, ir a Authentication > Providers
   - Habilitar Google
   - Configurar Client ID y Client Secret
   - Guardar cambios

### Facebook OAuth

1. **Configuración en Facebook Developers**:
   - Crear una aplicación en [Facebook Developers](https://developers.facebook.com/)
   - Configurar OAuth con los siguientes datos:
     - URIs de redirección válidos:
       - `https://[TU-PROYECTO].supabase.co/auth/v1/callback`
       - `http://localhost:5173/auth/callback/facebook` (para desarrollo)
       - `https://genia-frontendmpc.vercel.app/auth/callback/facebook` (para producción)
   - Obtener App ID y App Secret

2. **Configuración en Supabase**:
   - En el dashboard de Supabase, ir a Authentication > Providers
   - Habilitar Facebook
   - Configurar App ID y App Secret
   - Guardar cambios

## Implementación en el Backend

La implementación en el backend ya está realizada en el archivo `app/api/endpoints/auth.py`, que incluye:

- Endpoints para iniciar el flujo de autenticación con Google y Facebook
- Endpoints para procesar los callbacks de autenticación
- Lógica para crear o actualizar usuarios en Supabase
- Generación de tokens JWT para la sesión

## Implementación en el Frontend

A continuación se detalla la implementación necesaria en el frontend:

### 1. Configuración de Supabase Client

```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

export const supabase = createClient(supabaseUrl, supabaseAnonKey)
```

### 2. Componente de Inicio de Sesión

```tsx
// src/components/auth/LoginForm.tsx
import { useState } from 'react'
import { supabase } from '../../lib/supabase'

export const LoginForm = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })
      
      if (error) throw error
    } catch (error: any) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  const handleOAuthLogin = async (provider: 'google' | 'facebook') => {
    setLoading(true)
    setError(null)
    
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: `${window.location.origin}/auth/callback/${provider}`,
        },
      })
      
      if (error) throw error
    } catch (error: any) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-form">
      <h2>Iniciar Sesión</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleEmailLogin}>
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Cargando...' : 'Iniciar Sesión'}
        </button>
      </form>
      
      <div className="oauth-buttons">
        <button
          onClick={() => handleOAuthLogin('google')}
          disabled={loading}
          className="google-button"
        >
          Continuar con Google
        </button>
        
        <button
          onClick={() => handleOAuthLogin('facebook')}
          disabled={loading}
          className="facebook-button"
        >
          Continuar con Facebook
        </button>
      </div>
    </div>
  )
}
```

### 3. Componente de Registro

```tsx
// src/components/auth/RegisterForm.tsx
import { useState } from 'react'
import { supabase } from '../../lib/supabase'

export const RegisterForm = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            name,
          },
        },
      })
      
      if (error) throw error
    } catch (error: any) {
      setError(error.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-form">
      <h2>Crear Cuenta</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <form onSubmit={handleRegister}>
        <div className="form-group">
          <label htmlFor="name">Nombre</label>
          <input
            id="name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        
        <div className="form-group">
          <label htmlFor="password">Contraseña</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>
        
        <button type="submit" disabled={loading}>
          {loading ? 'Cargando...' : 'Registrarse'}
        </button>
      </form>
    </div>
  )
}
```

### 4. Manejador de Callback OAuth

```tsx
// src/pages/auth/OAuthCallback.tsx
import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { supabase } from '../../lib/supabase'

export const OAuthCallback = () => {
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const { provider } = useParams<{ provider: string }>()

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Procesar el callback de OAuth
        const { error } = await supabase.auth.getSession()
        
        if (error) {
          throw error
        }
        
        // Redirigir al dashboard después de iniciar sesión exitosamente
        navigate('/dashboard')
      } catch (error: any) {
        console.error('Error en callback OAuth:', error)
        setError(error.message)
        // Redirigir a la página de inicio de sesión en caso de error
        setTimeout(() => navigate('/login'), 3000)
      }
    }

    handleCallback()
  }, [navigate, provider])

  return (
    <div className="oauth-callback">
      {error ? (
        <div className="error-container">
          <h2>Error de autenticación</h2>
          <p>{error}</p>
          <p>Redirigiendo a la página de inicio de sesión...</p>
        </div>
      ) : (
        <div className="loading-container">
          <h2>Completando inicio de sesión...</h2>
          <div className="spinner"></div>
        </div>
      )}
    </div>
  )
}
```

### 5. Contexto de Autenticación

```tsx
// src/contexts/AuthContext.tsx
import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { Session, User } from '@supabase/supabase-js'
import { supabase } from '../lib/supabase'

type AuthContextType = {
  session: Session | null
  user: User | null
  loading: boolean
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [session, setSession] = useState<Session | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Obtener sesión inicial
    const getInitialSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession()
        setSession(session)
        setUser(session?.user ?? null)
      } catch (error) {
        console.error('Error al obtener sesión inicial:', error)
      } finally {
        setLoading(false)
      }
    }

    getInitialSession()

    // Escuchar cambios en la autenticación
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setSession(session)
        setUser(session?.user ?? null)
        setLoading(false)
      }
    )

    return () => {
      subscription.unsubscribe()
    }
  }, [])

  const signOut = async () => {
    try {
      await supabase.auth.signOut()
    } catch (error) {
      console.error('Error al cerrar sesión:', error)
    }
  }

  const value = {
    session,
    user,
    loading,
    signOut,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth debe ser usado dentro de un AuthProvider')
  }
  return context
}
```

### 6. Protección de Rutas

```tsx
// src/components/auth/ProtectedRoute.tsx
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'

export const ProtectedRoute = () => {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="loading">Cargando...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}
```

## Flujo de Autenticación

1. **Inicio de Sesión**:
   - El usuario accede a la página de inicio de sesión
   - Puede elegir entre iniciar sesión con email/contraseña o con un proveedor OAuth (Google/Facebook)
   - Al elegir un proveedor OAuth, es redirigido a la página de autorización del proveedor

2. **Autorización en el Proveedor**:
   - El usuario autoriza a la aplicación en la página del proveedor
   - El proveedor redirige de vuelta a la aplicación con un código de autorización

3. **Callback de OAuth**:
   - La aplicación recibe el código de autorización
   - Intercambia el código por tokens de acceso y actualización
   - Crea o actualiza el usuario en Supabase
   - Genera un token JWT para la sesión
   - Redirige al usuario al dashboard

4. **Sesión Activa**:
   - El token JWT se almacena en localStorage
   - El contexto de autenticación mantiene la información del usuario
   - Las rutas protegidas verifican la existencia de un usuario autenticado

5. **Cierre de Sesión**:
   - El usuario puede cerrar sesión en cualquier momento
   - Se elimina el token JWT y se redirige a la página de inicio de sesión

## Consideraciones de Seguridad

- Utilizar HTTPS en producción
- Configurar correctamente las URIs de redirección para prevenir ataques de redirección
- Validar tokens en el backend antes de permitir acceso a recursos protegidos
- Implementar expiración de tokens y renovación segura
- Seguir las mejores prácticas de OAuth 2.0 y OpenID Connect

## Pruebas

Para probar la implementación de OAuth:

1. Configurar variables de entorno en el frontend:
   ```
   VITE_SUPABASE_URL=https://[TU-PROYECTO].supabase.co
   VITE_SUPABASE_ANON_KEY=[anon/public key]
   ```

2. Iniciar la aplicación en modo desarrollo:
   ```
   cd genia_frontendMPC
   npm run dev
   ```

3. Acceder a la página de inicio de sesión y probar los diferentes métodos de autenticación
