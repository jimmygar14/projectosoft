import reflex as rx
import re
from . import builder


from supabase import create_client, Client
import os 

# --- Configuración de Supabase si vas a entrar a ver en supabase.com tienes que iniciar sesion con mi perfil
# es correo: garcialealjimmydejesus@gmail.com contraseña: 1047051717 esta es mi cuenta de google ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://arcwophrnygdpiouboli.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_4Qkr8vJXHFiVHmiaUIynVw_yy6_bRXR")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Conexión a Supabase inicializada correctamente.")
except Exception as e:
    print(f"Error al inicializar Supabase: {e}. Revisa las credenciales.")
    supabase = None

class SupabaseService:
    def __init__(self, client: Client):
        self.client = client
        self.table_name = "perfiles"

    def signup(self, email, password, fecha_nacimiento, pais):
        if not self.client: return {"error": "Conexión a Supabase no disponible."}

        try:
            auth_response = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            
            user = auth_response.user
            if not user:
                return {"error": "Error de registro en Auth. Revisa la configuración de Supabase."}
            
            user_id = user.id

        except Exception as e:
            error_message = e.args[0] if e.args else 'Error desconocido'
            return {"error": f"Error de autenticación: {error_message}"}

        try:
            self.client.table(self.table_name).insert({
                "id": user_id,
                "Usuario": email, 
                "Fecha": fecha_nacimiento, 
                "Pais": pais
            }).execute()

            return {"success": "Cuenta creada exitosamente. Revisa tu correo para verificar la cuenta."}

        except Exception as e:
            error_msg = str(e)
            
            if 'violates row-level security policy' in error_msg:
                 return {"success": "Registro de cuenta exitoso. "}
            elif 'duplicate key value violates unique constraint' in error_msg:
                 return {"error": "El usuario ya existe o hubo un conflicto de ID."}
            elif 'invalid input syntax for type' in error_msg:
                 return {"error": "Error de tipo de columna. ¿El 'id' de la tabla 'perfiles' es 'uuid'?"}
            else:
                 return {"error": f"Error de base de datos: {error_msg.splitlines()[0]}"}

    def login(self, email, password):
        if not self.client: return {"error": "Conexión a Supabase no disponible."}
        
        try:
            auth_response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if auth_response.user:
                return {"success": "Inicio de sesión exitoso."}
            else:
                return {"error": "Credenciales incorrectas o usuario no verificado."}
                
        except Exception as e:
            return {"error": "Credenciales incorrectas. Intenta de nuevo."}


SUPABASE_SERVICE = SupabaseService(supabase)


# -------------------------
# ANIMACIONES CSS (GLOBAL)
# -------------------------
CSS_KEYFRAMES = """
@keyframes pulse_color {
    0% { opacity: 0.6; }
    50% { opacity: 0.9; }
    100% { opacity: 0.6; }
}
@keyframes float_and_grow {
    0% { transform: translateY(0px) scale(1.0); }
    50% { transform: translateY(-15px) scale(1.1); } 
    100% { transform: translateY(0px) scale(1.0); }
}
"""

# -------------------------
# COMPONENTE REUTILIZABLE: Esfera Animada
# -------------------------
def animated_sphere(
    top: str, left: str, right: str, bottom: str, width: str, height: str, spin_duration: str, pulse_duration: str, delay: str
):
    return rx.box(
        bg="radial-gradient(ellipse, #AA14F0 0%, rgba(170,20,240,0.0) 70%)",
        width=width,
        height=height,
        position="absolute",
        top=top,
        left=left,
        right=right,
        bottom=bottom,
        animation=f"float_and_grow {spin_duration} ease-in-out {delay} infinite alternate, pulse_color {pulse_duration} ease-in-out {delay} infinite",
        z_index=0,
    )

# -------------------------
# COMPONENTE REUTILIZABLE: Selector AMD/INTEL
# -------------------------
def chip_selector(logo_url: str, alt_text: str, route: str, color: str):
    return rx.vstack(
        rx.image(
            src=logo_url,
            alt=alt_text,
            width="150px",
            height="auto",
            margin_y="20px",
        ),
        
        rx.box(
            position="absolute",
            top="0", left="0", right="0", bottom="0",
            border_radius="12px",
            border=f"3px solid {color}",
            opacity=0,
            transition="opacity 0.2s ease-in-out, transform 0.2s ease-in-out",
            _hover={
                "opacity": 1,
                "transform": "scale(1.05)",
            }
        ),

        on_click=lambda: rx.redirect(route),
        width="220px",
        height="180px",
        padding="15px",
        border_radius="12px",
        bg="rgba(0, 0, 0, 0.4)",
        justify="center",
        align="center",
        position="relative",
        cursor="pointer",
        transition="transform 0.2s ease-in-out",
        box_shadow="0 4px 15px rgba(0, 0, 0, 0.5)",
        _active={
            "transform": "scale(0.98)",
        }
    )


# -------------------------
# ESTADO LOGIN
# -------------------------
class State(rx.State):
    email: str = ""
    password: str = ""
    error_msg: str = "Bienvenido"

    # Función para limpiar los campos al entrar a la página
    def on_mount(self):
        self.email = ""
        self.password = ""
        self.error_msg = "Bienvenido"

    def validar_email(self, text: str) -> bool:
        patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(patron, text) is not None

    def login(self):
        self.error_msg = "" 

        if not self.email:
            self.error_msg = "❌ El correo no puede estar vacío."
            return
        if not self.password:
            self.error_msg = "❌ La contraseña no puede estar vacía."
            return

        if not self.validar_email(self.email):
            self.error_msg = "❌ Correo inválido."
            return
        
        if self.email == "admin@gmail.com" and self.password == "123456":
            return rx.redirect("/") 
        
        result = SUPABASE_SERVICE.login(self.email, self.password)
        if "success" in result:
             return rx.redirect("/")
        else:
            self.error_msg = "❌ Correo o contraseña incorrectos."

# -------------------------
# ESTADO CREAR CUENTA
# -------------------------
class CreateAccountState(rx.State):
    email: str = ""
    password: str = ""
    birthdate: str = ""
    location: str = ""
    error_msg: str = ""

    def on_mount(self):
        self.email = ""
        self.password = ""
        self.birthdate = ""
        self.location = ""
        self.error_msg = ""

    def validar_email(self, text: str) -> bool:
        patron = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        return re.match(patron, text) is not None
    
    def create_account(self):
        self.error_msg = "" 

        if not all([self.email, self.password, self.birthdate, self.location]):
            self.error_msg = "❌ Todos los campos son obligatorios."
            return
        
        if not self.validar_email(self.email):
            self.error_msg = "❌ Formato de correo inválido."
            return

        result = SUPABASE_SERVICE.signup(
             self.email, 
             self.password, 
             self.birthdate, 
             self.location
        )

        if "success" in result:
             return rx.redirect("/login")
        else:
             self.error_msg = f"❌ {result.get('error', 'Error al crear cuenta')}"


# -------------------------
# PÁGINA HOME (PRINCIPAL)
# -------------------------
def home():
    return rx.box(
        rx.html(f"<style>{CSS_KEYFRAMES}</style>"),
        
        rx.box(
            animated_sphere(
                top="3%", left="34%", right="auto", bottom="auto", 
                width="200px", height="200px", spin_duration="8s", pulse_duration="7s", delay="1s" 
            ),
            animated_sphere(
                top="10%", left="auto", right="4.2%", bottom="auto", 
                width="200px", height="200px", spin_duration="7s", pulse_duration="6s", delay="1.5s"
            ),
            animated_sphere(
                top="auto", left="auto", right="8%", bottom="8%", 
                width="150px", height="150px", spin_duration="5s", pulse_duration="8s", delay="3s" 
            ),
            animated_sphere(
                top="auto", left="auto", right="41%", bottom="25%", 
                width="250px", height="250px", spin_duration="9s", pulse_duration="5s", delay="4.5s"
            ),
            animated_sphere(
                top="64%", left="4%", right="auto", bottom="auto", 
                width="250px", height="250px", spin_duration="4s", pulse_duration="9s", delay="6s" 
            ),
            position="absolute",
            width="100%", height="100%",
            overflow="hidden",
            z_index=0,
        ),
        
        rx.center(
            rx.vstack(
                rx.text("¡Bienvenido a nuestro E-commerce!", size="9", weight="bold", color="white"),
                rx.text("Explora nuestros productos o inicia sesión para acceder a tu cuenta.", color="rgba(255,255,255,0.7)"),
                
                rx.divider(size="4", style={"border_color": "rgba(255,255,255,0.2)", "margin_y": "20px"}),
                
                rx.text("Selecciona tu plataforma para comenzar:", color="white", size="5", margin_y="10px"),
                rx.hstack(
                    chip_selector(
                        logo_url="https://1000marcas.net/wp-content/uploads/2020/03/Logo-AMD.png", 
                        alt_text="AMD Logo",
                        route="/builder/amd", 
                        color="#35A535" 
                    ),
                    rx.box(width="20px"), 
                    chip_selector(
                        logo_url="https://1000marcas.net/wp-content/uploads/2020/02/Intel-Logo-2005.png", 
                        alt_text="Intel Logo",
                        route="/builder/intel", 
                        color="#0071C5" 
                    ),
                    spacing="5",
                    margin_bottom="30px", 
                ),
                
                rx.button(
                    "Iniciar Sesión",
                    size="4",
                    bg="linear-gradient(90deg,#501794, #3E70A1)",
                    color="white",
                    border_radius="8px",
                    on_click=lambda: rx.redirect("/login"), 
                    width="200px" 
                ),
                
                spacing="5",
                align="center",
                padding="20px",
                z_index=1 
            ),
            height="100vh", 
            width="100%",
        ),
        
        bg="linear-gradient(135deg, #120024, #29004A)",
        height="100vh", 
        width="100%",
        position="relative",
        overflow="hidden",
    )


# -------------------------
# PÁGINA LOGIN
# -------------------------
def login_page():
    return rx.box(
        rx.html(f"<style>{CSS_KEYFRAMES}</style>"),
        
        rx.tooltip(
            rx.icon(
                tag="arrow_left",
                size=30,
                color="white",
                cursor="pointer",
                on_click=lambda: rx.redirect("/"),
                position="absolute",
                top="20px",
                left="20px",
                z_index=50,
            ),
            content="Volver al inicio",
        ),

        rx.box(
            animated_sphere(
                top="3%", left="34%", right="auto", bottom="auto", 
                width="200px", height="200px", spin_duration="8s", pulse_duration="7s", delay="1s" 
            ),
            animated_sphere(
                top="10%", left="auto", right="4.2%", bottom="auto", 
                width="200px", height="200px", spin_duration="7s", pulse_duration="6s", delay="1.5s"
            ),
            animated_sphere(
                top="auto", left="auto", right="8%", bottom="8%", 
                width="150px", height="150px", spin_duration="5s", pulse_duration="8s", delay="3s" 
            ),
            animated_sphere(
                top="auto", left="auto", right="41%", bottom="25%", 
                width="250px", height="250px", spin_duration="9s", pulse_duration="5s", delay="4.5s"
            ),
            animated_sphere(
                top="64%", left="4%", right="auto", bottom="auto", 
                width="250px", height="250px", spin_duration="4s", pulse_duration="9s", delay="6s" 
            ),
            position="absolute",
            width="100%", height="100%",
            overflow="hidden",
            z_index=0,
        ),

        rx.flex(
            rx.center(
                rx.vstack(
                    rx.image(src="logo.png", width="230px", height="230px"), 
                    rx.text("RENDIMIENTO", size="9", color="white", font_family="Porter Sans Block"),
                    rx.text("SIN LIMITES", size="7", color="rgba(255,255,255,0.7)", font_family="Porter Sans Block"),
                    spacing="4",
                    align="center",
                ),
                flex="1",
                z_index=1,
            ),

            rx.center(
                rx.vstack(
                    rx.text("INICIAR SESIÓN", size="9", align="center", weight="bold", color="white"),
                    rx.text("Accede a tu cuenta", color="rgba(255,255,255,0.7)"), 

                    rx.input(
                        placeholder="Correo electrónico",
                        type="email",
                        value=State.email,
                        on_change=State.set_email,
                        bg="rgba(255,255,255,0.1)",
                        color="white",
                        padding="10px",
                        border_radius="8px",
                        width="100%",
                        _placeholder={"color": "rgba(255,255,255,0.5)"}
                    ),

                    rx.input(
                        placeholder="Contraseña",
                        type="password",
                        value=State.password,
                        on_change=State.set_password,
                        bg="rgba(255,255,255,0.1)",
                        color="white",
                        padding="10px",
                        border_radius="8px",
                        width="100%",
                        _placeholder={"color": "rgba(255,255,255,0.5)"}
                    ),

                    rx.text(
                        State.error_msg, 
                        color=rx.cond(
                            State.error_msg.startswith("❌"), 
                            "red", 
                            "white"
                        ),
                        weight="bold",
                        font_size="1em",
                        align="center",
                    ),

                    rx.button(
                        "Iniciar sesión",
                        size="4",
                        align="center",
                        width="100%",
                        bg="linear-gradient(90deg,#501794, #3E70A1)",
                        color="white",
                        border_radius="8px",
                        on_click=State.login,
                    ),

                    rx.button(
                        "Crear cuenta",
                        size="3",
                        width="100%",
                        variant="outline",
                        color="white",
                        border_color="white",
                        border_radius="8px",
                        margin_top="10px",
                        on_click=lambda: rx.redirect("/create-account"),
                    ),

                    rx.button(
                        rx.hstack(
                            rx.icon(tag="facebook", size=18),
                            rx.text("Iniciar sesión con Facebook", margin_left="-5px"),
                        ),
                        size="3",
                        width="100%",
                        bg="#1877F2",
                        color="white",
                        border_radius="8px",
                        on_click=lambda: rx.redirect("https://www.facebook.com/login.php"),
                    ),

                    rx.button(
                        rx.hstack(
                            rx.icon(tag="chrome", size=18, color="black"),
                            rx.text("Iniciar sesión con Google", color="black", margin_left="-5px"),
                        ),
                        size="3",
                        width="100%",
                        bg="white",
                        color="black",
                        border_radius="8px",
                        on_click=lambda: rx.redirect("https://accounts.google.com/signin"),
                    ),

                    spacing="4",
                    align="center",
                    width="300px",
                ),
                flex="1",
                z_index=1,
            ),
            align="center",
            justify="center",
            width="100%",
            height="100vh",
            position="relative",
            z_index=1,
        ),
        
        # --- on_mount y estilos deben ir al final ---
        on_mount=State.on_mount,
        bg="linear-gradient(135deg, #120024, #29004A)",
        height="100vh", 
        width="100%",
        position="relative",
        overflow="hidden",
    )


# -------------------------
# PÁGINA CREAR CUENTA
# -------------------------
def create_account_page():
    return rx.box(
        rx.html(f"<style>{CSS_KEYFRAMES}</style>"),
        
        rx.tooltip(
            rx.icon(
                tag="arrow_left", 
                size=30,
                color="white",
                cursor="pointer",
                on_click=lambda: rx.redirect("/login"), 
                position="absolute",
                top="20px",
                left="20px",
                z_index=50,
            ),
            content="Volver al inicio de sesión",
        ),

        rx.box(
            animated_sphere(top="3%", left="34%", right="auto", bottom="auto", width="200px", height="200px", spin_duration="8s", pulse_duration="7s", delay="1s"),
            animated_sphere(top="10%", left="auto", right="4.2%", bottom="auto", width="200px", height="200px", spin_duration="7s", pulse_duration="6s", delay="1.5s"),
            animated_sphere(top="auto", left="auto", right="8%", bottom="8%", width="150px", height="150px", spin_duration="5s", pulse_duration="8s", delay="3s"),
            animated_sphere(top="auto", left="auto", right="41%", bottom="25%", width="250px", height="250px", spin_duration="9s", pulse_duration="5s", delay="4.5s"),
            animated_sphere(top="64%", left="4%", right="auto", bottom="auto", width="250px", height="250px", spin_duration="4s", pulse_duration="9s", delay="6s"),
            position="absolute",
            width="100%", height="100%",
            overflow="hidden",
            z_index=0,
        ),

        rx.flex(
            rx.center(
                rx.vstack(
                    rx.image(src="logo.png", width="230px", height="230px"),
                    rx.text("RENDIMIENTO", size="9", color="white", font_family="Porter Sans Block"),
                    rx.text("SIN LIMITES", size="7", color="rgba(255,255,255,0.7)", font_family="Porter Sans Block"),
                    spacing="4",
                    align="center",
                ),
                flex="1",
                z_index=1,
            ),

            rx.center(
                rx.vstack(
                    rx.text("CREAR CUENTA", size="9", weight="bold", color="white"),
                    rx.text("Rellena tus datos a continuación", color="rgba(255,255,255,0.7)"),

                    rx.input(
                        placeholder="Correo electrónico",
                        type="email",
                        value=CreateAccountState.email,
                        on_change=CreateAccountState.set_email,
                        bg="rgba(255,255,255,0.1)",
                        color="white",
                        padding="10px",
                        border_radius="8px",
                        width="100%",
                        _placeholder={"color": "rgba(255,255,255,0.5)"}
                    ),

                    rx.input(
                        placeholder="Contraseña",
                        type="password",
                        value=CreateAccountState.password,
                        on_change=CreateAccountState.set_password,
                        bg="rgba(255,255,255,0.1)",
                        color="white",
                        padding="10px",
                        border_radius="8px",
                        width="100%",
                        _placeholder={"color": "rgba(255,255,255,0.5)"}
                    ),

                    rx.input(
                        placeholder="Fecha de nacimiento", 
                        type="date",
                        value=CreateAccountState.birthdate,
                        on_change=CreateAccountState.set_birthdate,
                        bg="rgba(255,255,255,0.1)",
                        color="white",
                        padding="10px",
                        border_radius="8px",
                        width="100%",
                        _placeholder={"color": "rgba(255,255,255,0.5)"}
                    ),

                    rx.input(
                        placeholder="País",
                        type="text",
                        value=CreateAccountState.location,
                        on_change=CreateAccountState.set_location,
                        bg="rgba(255,255,255,0.1)",
                        color="white",
                        padding="10px",
                        border_radius="8px",
                        width="100%",
                        _placeholder={"color": "rgba(255,255,255,0.5)"}
                    ),

                    rx.text(
                        CreateAccountState.error_msg, 
                        color="red",
                        weight="bold",
                        font_size="1em",
                        align="center",
                    ),

                    rx.button(
                        "Crear cuenta",
                        size="4",
                        width="100%",
                        bg="linear-gradient(90deg,#501794, #3E70A1)",
                        color="white",
                        border_radius="8px",
                        on_click=CreateAccountState.create_account,
                    ),
                    
                    rx.button(
                        "Ya tengo una cuenta (Iniciar Sesión)",
                        size="3",
                        width="100%",
                        variant="outline",
                        color="white",
                        border_color="white",
                        border_radius="8px",
                        margin_top="10px",
                        on_click=lambda: rx.redirect("/login"),
                    ),

                    spacing="4",
                    align="center",
                    width="300px",
                ),
                flex="1",
                z_index=1,
            ),
            align="center",
            justify="center",
            width="100%",
            height="100vh",
            position="relative",
            z_index=1,
        ),

        # --- on_mount y estilos deben ir al final ---
        on_mount=CreateAccountState.on_mount,
        bg="linear-gradient(135deg, #120024, #29004A)",
        height="100vh", 
        width="100%",
        position="relative",
        overflow="hidden",
    )


# --- APP ---
app = rx.App()
app.add_page(home, route="/")
app.add_page(login_page, route="/login")
app.add_page(create_account_page, route="/create-account")
