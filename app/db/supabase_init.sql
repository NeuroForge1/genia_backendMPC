-- Script SQL para crear la estructura de la base de datos en Supabase

-- Función para actualizar el campo updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
  id UUID PRIMARY KEY REFERENCES auth.users(id),
  email TEXT UNIQUE NOT NULL,
  name TEXT,
  plan TEXT DEFAULT 'free',
  creditos INTEGER DEFAULT 100,
  modulos_activos JSONB DEFAULT '["openai", "whatsapp_basic"]',
  is_active BOOLEAN DEFAULT TRUE,
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  stripe_subscription_status TEXT,
  avatar_url TEXT,
  referral_code TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger para actualizar el campo updated_at en usuarios
CREATE TRIGGER update_usuarios_updated_at
BEFORE UPDATE ON usuarios
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Tabla de herramientas disponibles
CREATE TABLE IF NOT EXISTS herramientas_disponibles (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nombre TEXT NOT NULL,
  descripcion TEXT,
  plan_minimo TEXT DEFAULT 'free',
  coste_creditos INTEGER DEFAULT 1,
  activa BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger para actualizar el campo updated_at en herramientas_disponibles
CREATE TRIGGER update_herramientas_disponibles_updated_at
BEFORE UPDATE ON herramientas_disponibles
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Tabla de herramientas conectadas (OAuth)
CREATE TABLE IF NOT EXISTS herramientas_conectadas (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
  servicio TEXT NOT NULL,
  access_token TEXT NOT NULL,
  refresh_token TEXT,
  expiracion TIMESTAMP WITH TIME ZONE,
  estado BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  UNIQUE(user_id, servicio)
);

-- Trigger para actualizar el campo updated_at en herramientas_conectadas
CREATE TRIGGER update_herramientas_conectadas_updated_at
BEFORE UPDATE ON herramientas_conectadas
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Tabla de tareas generadas
CREATE TABLE IF NOT EXISTS tareas_generadas (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
  herramienta TEXT NOT NULL,
  capability TEXT NOT NULL,
  params JSONB,
  resultado JSONB,
  creditos_consumidos INTEGER DEFAULT 0,
  fecha TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de plantillas de contenido
CREATE TABLE IF NOT EXISTS plantillas_contenido (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nombre TEXT NOT NULL,
  descripcion TEXT,
  categoria TEXT,
  prompt TEXT NOT NULL,
  parametros JSONB,
  plan_minimo TEXT DEFAULT 'free',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger para actualizar el campo updated_at en plantillas_contenido
CREATE TRIGGER update_plantillas_contenido_updated_at
BEFORE UPDATE ON plantillas_contenido
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Tabla de plantillas de usuario
CREATE TABLE IF NOT EXISTS plantillas_usuario (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
  nombre TEXT NOT NULL,
  descripcion TEXT,
  prompt TEXT NOT NULL,
  parametros JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Trigger para actualizar el campo updated_at en plantillas_usuario
CREATE TRIGGER update_plantillas_usuario_updated_at
BEFORE UPDATE ON plantillas_usuario
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Políticas de seguridad (RLS)

-- Habilitar RLS para todas las tablas
ALTER TABLE usuarios ENABLE ROW LEVEL SECURITY;
ALTER TABLE herramientas_conectadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE tareas_generadas ENABLE ROW LEVEL SECURITY;
ALTER TABLE plantillas_usuario ENABLE ROW LEVEL SECURITY;

-- Políticas para la tabla usuarios
CREATE POLICY admin_all_usuarios ON usuarios
  USING (auth.uid() IN (SELECT id FROM usuarios WHERE plan = 'admin'))
  WITH CHECK (auth.uid() IN (SELECT id FROM usuarios WHERE plan = 'admin'));

CREATE POLICY user_own_profile ON usuarios
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Políticas para la tabla herramientas_conectadas
CREATE POLICY admin_all_herramientas_conectadas ON herramientas_conectadas
  USING (auth.uid() IN (SELECT id FROM usuarios WHERE plan = 'admin'))
  WITH CHECK (auth.uid() IN (SELECT id FROM usuarios WHERE plan = 'admin'));

CREATE POLICY user_own_connections ON herramientas_conectadas
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Políticas para la tabla tareas_generadas
CREATE POLICY admin_all_tareas_generadas ON tareas_generadas
  USING (auth.uid() IN (SELECT id FROM usuarios WHERE plan = 'admin'));

CREATE POLICY user_own_tasks ON tareas_generadas
  USING (auth.uid() = user_id);

-- Políticas para la tabla plantillas_usuario
CREATE POLICY admin_all_plantillas_usuario ON plantillas_usuario
  USING (auth.uid() IN (SELECT id FROM usuarios WHERE plan = 'admin'))
  WITH CHECK (auth.uid() IN (SELECT id FROM usuarios WHERE plan = 'admin'));

CREATE POLICY user_own_templates ON plantillas_usuario
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Índices para optimizar consultas
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
CREATE INDEX IF NOT EXISTS idx_usuarios_stripe_customer_id ON usuarios(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_tareas_generadas_user_id ON tareas_generadas(user_id);
CREATE INDEX IF NOT EXISTS idx_tareas_generadas_herramienta ON tareas_generadas(herramienta);
CREATE INDEX IF NOT EXISTS idx_herramientas_conectadas_user_servicio ON herramientas_conectadas(user_id, servicio);

-- Datos iniciales para herramientas disponibles
INSERT INTO herramientas_disponibles (nombre, descripcion, plan_minimo, coste_creditos, activa) VALUES
('openai', 'Generación de texto y procesamiento de lenguaje natural con OpenAI', 'free', 1, true),
('whatsapp', 'Envío y recepción de mensajes de WhatsApp', 'basic', 5, true),
('stripe', 'Procesamiento de pagos y gestión de suscripciones', 'pro', 10, true),
('gmail', 'Envío de correos electrónicos a través de Gmail', 'basic', 3, true),
('content', 'Generación de contenido optimizado para marketing', 'basic', 5, true),
('funnels', 'Creación y gestión de embudos de ventas', 'pro', 15, true);

-- Datos iniciales para plantillas de contenido
INSERT INTO plantillas_contenido (nombre, descripcion, categoria, prompt, parametros, plan_minimo) VALUES
('Post Instagram', 'Genera un post atractivo para Instagram', 'social_media', 'Crea un post para Instagram sobre {{tema}} con tono {{tono}} y {{longitud}} caracteres. {{incluir_hashtags}}', '{"tema": "string", "tono": "string", "longitud": "string", "incluir_hashtags": "boolean"}', 'free'),
('Email Marketing', 'Genera un email de marketing persuasivo', 'email', 'Crea un email de marketing para {{producto}} dirigido a {{audiencia}} con el objetivo de {{objetivo}}. {{incluir_cta}}', '{"producto": "string", "audiencia": "string", "objetivo": "string", "incluir_cta": "boolean"}', 'basic'),
('Artículo Blog SEO', 'Genera un artículo de blog optimizado para SEO', 'blog', 'Escribe un artículo de blog sobre {{titulo}} incluyendo las palabras clave {{keywords}}. El artículo debe tener aproximadamente {{palabras}} palabras y un tono {{tono}}.', '{"titulo": "string", "keywords": "array", "palabras": "integer", "tono": "string"}', 'pro');
