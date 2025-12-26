import streamlit as st
from groq import Groq
import secrets
import mysql.connector
import time

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN GENERAL DE LA APP
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AsistenteIA - Chat Inteligente",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos personalizados
st.markdown("""
    <style>
    .main-title {
        text-align: center;
        color: #1f77e1;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        color: #6c757d;
        font-size: 14px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<h1 class="main-title">🤖 AsistenteIA</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Tu asistente inteligente potenciado por IA avanzada</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE MODELOS
# ─────────────────────────────────────────────────────────────
MODELOS = {
    'Rápido (8B)': 'llama-3.1-8b-instant',
    'Potente (70B)': 'llama-3.3-70b-versatile',
}

SECCIONES = {
    "🏠 Inicio": "inicio",
    "📝 Chat": "chat",
    "⚙️ Configuración": "config"
}

# ─────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE GROQ
# ─────────────────────────────────────────────────────────────
@st.cache_resource
def crear_cliente_groq():
    """Crea y cachea el cliente de Groq para optimizar performance"""
    try:
        clave_secreta = st.secrets.get("CLAVE_API")
        if not clave_secreta:
            st.error("❌ Error: No se encontró la CLAVE_API en secrets.toml")
            return None
        return Groq(api_key=clave_secreta)
    except Exception as e:
        st.error(f"❌ Error al conectar con Groq: {str(e)}")
        return None

# ─────────────────────────────────────────────────────────────
# MANEJO DE SESIÓN
# ─────────────────────────────────────────────────────────────
def inicializar_sesion():
    """Inicializa variables de sesión necesarias"""
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []
    if "usuario_nombre" not in st.session_state:
        st.session_state.usuario_nombre = "Usuario"
    if "contador_mensajes" not in st.session_state:
        st.session_state.contador_mensajes = 0


def agregar_mensaje(rol: str, contenido: str):
    """Agrega un mensaje al historial de chat"""
    # Intentar guardar el mensaje en la base de datos (si hay conexión)
    try:
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO mensajes (usuario, mensaje) VALUES (%s, %s)", (st.session_state.usuario_nombre, contenido))
            conn.commit()
            cursor.close()
    except Exception as e:
        st.warning(f"No se pudo guardar el mensaje en la base de datos: {e}")
    # Agregar el mensaje al historial de chat
    st.session_state.mensajes.append({
        "role": rol,
        "content": contenido,
        "timestamp": time.time()
    })
    if rol == "user":
        st.session_state.contador_mensajes += 1


# ─────────────────────────────────────────────────────────────
# INTERFAZ DEL CHAT
# ─────────────────────────────────────────────────────────────
def mostrar_historial_chat():
    """Muestra el historial de mensajes con mejor formato"""
    for mensaje in st.session_state.mensajes:
        rol = mensaje["role"]
        contenido = mensaje["content"]
        avatar = "🤖" if rol == "assistant" else "👤"
        
        with st.chat_message(rol, avatar=avatar):
            st.markdown(contenido)

# ─────────────────────────────────────────────────────────────
# INTERACCIÓN CON GROQ
# ─────────────────────────────────────────────────────────────
def obtener_respuesta_ia(cliente, modelo: str, mensaje: str):
    """
    Obtiene respuesta de la IA con streaming optimizado
    """
    try:
        with st.spinner("⏳ Pensando..."):
            respuesta = cliente.chat.completions.create(
                model=modelo,
                messages=[{"role": "user", "content": mensaje}],
                stream=True,
                temperature=0.7,
                max_tokens=2048
            )

            texto_final = ""
            placeholder = st.empty()
            
            for chunk in respuesta:
                parte = chunk.choices[0].delta.content or ""
                texto_final += parte
                placeholder.markdown(texto_final + "▌")
            
            placeholder.markdown(texto_final)
            return texto_final
            
    except Exception as e:
        st.error(f"❌ Error al obtener respuesta: {str(e)}")
        return None


# ─────────────────────────────────────────────────────────────
# SECCIONES DE LA APP
# ─────────────────────────────────────────────────────────────
def seccion_inicio():
    """Página de bienvenida con instrucciones"""
    st.header("👋 Bienvenido")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### 🎯 ¿Qué puedes hacer?
        
        - 💬 **Chat inteligente**: Conversa con IA avanzada
        - ⚡ **Respuestas rápidas**: Obtén información al instante
        - 🧠 **Múltiples modelos**: Elige entre diferentes IA
        - 🔒 **Privado y seguro**: Tus datos están protegidos
        """)
    
    with col2:
        st.markdown("""
        ### 📊 Estadísticas
        
        - **Mensajes enviados**: {0}
        - **Modelo actual**: {1}
        - **Versión**: 2.0
        - **Estado**: ✅ Operativo
        """.format(
            st.session_state.contador_mensajes,
            st.session_state.get("modelo_seleccionado", "No seleccionado")
        ))
    
    st.divider()
    st.markdown("""
    ### 🚀 Cómo empezar
    1. Ve a la sección **Chat**
    2. Selecciona un modelo en la barra lateral
    3. Escribe tu pregunta y presiona Enter
    4. ¡La IA responderá en segundos!
    """)


def seccion_chat(cliente, modelo):
    """Sección principal del chat"""
    st.header("💬 Chat")
    
    # Mostrar información del modelo
    info_col1, info_col2 = st.columns([1, 1])
    with info_col1:
        st.caption(f"📌 Modelo: {modelo}")
    with info_col2:
        if st.button("🗑️ Limpiar historial", key="limpiar_chat"):
            st.session_state.mensajes = []
            st.rerun()
    
    st.divider()
    
    # Contenedor del chat
    chat_container = st.container(height=500, border=True)
    with chat_container:
        mostrar_historial_chat()
    
    # Input de mensaje
    mensaje_usuario = st.chat_input("Escribe tu pregunta...")
    
    if mensaje_usuario:
        # Agregar mensaje del usuario
        agregar_mensaje("user", mensaje_usuario)
        
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(mensaje_usuario)
        
        # Obtener respuesta de IA
        respuesta = obtener_respuesta_ia(cliente, modelo, mensaje_usuario)
        
        if respuesta:
            agregar_mensaje("assistant", respuesta)
            st.rerun()


def seccion_configuracion():
    """Sección de configuración del usuario"""
    st.header("⚙️ Configuración")
    
    st.subheader("👤 Perfil de usuario")
    nombre = st.text_input(
        "Tu nombre:",
        value=st.session_state.usuario_nombre,
        key="nombre_usuario"
    )
    st.session_state.usuario_nombre = nombre
    
    st.divider()
    st.subheader("🔧 Preferencias de chat")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        st.caption(f"📊 Total de mensajes: {st.session_state.contador_mensajes}")
    with col2:
        st.caption("🕐 Última sesión: Activa")
    
    st.divider()
    st.markdown("### ℹ️ Información del sistema")
    st.info("""
    - **Plataforma**: Streamlit
    - **IA**: Groq (LLaMA 3)
    - **Version**: 2.0
    - **Status**: ✅ En línea
    """)
 #─────────────────────────────────────────────────────────────
 # Configuración de la base de datos
 #─────────────────────────────────────────────────────────────
usuario_db = "tu_usuario"
contrasena_db = "tu_contrasena"
host_db = "localhost"
nombre_db = "asistentia"

# Inicialmente no conectamos la DB hasta confirmar disponibilidad
conn = None

def crear_conexion_db():
    """Intenta crear y devolver la conexión a la base de datos. Devuelve None si falla."""
    global conn
    try:
        conn = mysql.connector.connect(
            user=usuario_db,
            password=contrasena_db,
            host=host_db,
            database=nombre_db
        )
        return conn
    except Exception as e:
        st.warning(f"Advertencia: no se pudo conectar a la base de datos: {e}")
        conn = None
        return None

# ─────────────────────────────────────────────────────────────
# EJECUCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────────
def main():
    # Inicializar sesión
    inicializar_sesion()
    
    # Barra lateral
    with st.sidebar:
        st.title("⚙️ Panel de Control")
        st.divider()
        
        # Selector de sección
        seccion_actual = st.selectbox(
            "📂 Navegación",
            options=list(SECCIONES.keys()),
            format_func=lambda x: x,
            key="seccion_select"
        )
        
        st.divider()
        
        # Selector de modelo (solo para chat)
        st.subheader("🤖 Modelo IA")
        modelo_seleccionado = st.selectbox(
            "Elige un modelo:",
            options=list(MODELOS.keys()),
            help="Modelos disponibles con diferentes capacidades"
        )
        st.session_state.modelo_seleccionado = modelo_seleccionado
        modelo_key = MODELOS[modelo_seleccionado]
        
        st.divider()
        
        # Información útil
        with st.expander("ℹ️ Ayuda"):
            st.markdown("""
            **Preguntas que puedo responder:**
            - Preguntas generales
            - Ayuda con programación
            - Análisis de textos
            - Explicaciones complejas
            """)
    
    # Conectar con Groq
    # Intentar conectar a la base de datos (no detiene la app si falla)
    crear_conexion_db()

    cliente = crear_cliente_groq()
    
    if not cliente:
        st.error("No se pudo conectar con la IA. Verifica tu configuración.")
        return
    
    # Mostrar sección seleccionada
    if SECCIONES[seccion_actual] == "inicio":
        seccion_inicio()
    elif SECCIONES[seccion_actual] == "chat":
        # Pasamos el identificador real del modelo (modelo_key) en lugar
        # del nombre mostrado (modelo_seleccionado) para evitar errores
        # 'model_not_found' cuando la API espera el id técnico.
        seccion_chat(cliente, modelo_key)
    elif SECCIONES[seccion_actual] == "config":
        seccion_configuracion()


if __name__ == "__main__": 
    main() 