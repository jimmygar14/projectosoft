import reflex as rx
import re
from supabase import create_client, Client
import os 
from . import  builder

# --- Configuración de Supabase ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://arcwophrnygdpiouboli.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_4Qkr8vJXHFiVHmiaUIynVw_yy6_bRXR")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("Conexión a Supabase inicializada correctamente.")
except Exception as e:
    print(f"Error al inicializar Supabase: {e}")
    supabase = None

# --- Servicios Supabase ---
class SupabaseService:
    def __init__(self, client: Client):
        self.client = client
        self.table_name = "perfiles"

    def signup(self, email, password, fecha_nacimiento, pais):
        if not self.client: return {"error": "Conexión a Supabase no disponible."}
        try:
            auth_response = self.client.auth.sign_up({"email": email, "password": password})
            user = auth_response.user
            if not user:
                return {"error": "Error de registro en Auth."}
            user_id = user.id
        except Exception as e:
            error_message = e.args[0] if e.args else 'Error desconocido'
            return {"error": f"Error de autenticación: {error_message}"}

        try:
            self.client.table(self.table_name).insert({
                "id": user_id, "Usuario": email, "Fecha": fecha_nacimiento, "Pais": pais
            }).execute()
            return {"success": "Cuenta creada exitosamente."}
        except Exception as e:
            error_msg = str(e)
            if 'violates row-level security policy' in error_msg:
                return {"success": "Registro exitoso."}
            elif 'duplicate key value' in error_msg:
                return {"error": "El usuario ya existe."}
            else:
                return {"error": f"Error de base de datos: {error_msg.splitlines()[0]}"}

    def login(self, email, password):
        if not self.client: return {"error": "Conexión a Supabase no disponible."}
        try:
            auth_response = self.client.auth.sign_in_with_password({"email": email, "password": password})
            if auth_response.user:
                return {"success": "Inicio de sesión exitoso."}
            else:
                return {"error": "Credenciales incorrectas."}
        except Exception as e:
            return {"error": "Credenciales incorrectas."}

SUPABASE_SERVICE = SupabaseService(supabase)

# --- CSS KEYFRAMES ---
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

# --- MODELOS ---
class Producto(rx.Base):
    id: str = "" 
    nombre: str = ""
    precio: float = 0.0
    imagen: str = ""
    categoria: str = ""
    marca: str = ""
    socket: str = ""

class CartItem(rx.Base):
    id: str = "" 
    nombre: str = ""
    precio: float = 0.0
    imagen: str = ""
    cantidad: int = 1

def background_spheres():
    """Componente reutilizable para las esferas de fondo animadas"""
    return rx.box(
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
    )

# --- ESTADOS (STATES) ---

class AuthState(rx.State):
    """Estado para manejar la autenticación y redirección"""
    is_authenticated: bool = False
    
    def check_auth(self):
        """Verificar si el usuario está autenticado"""
        # Por ahora, asumimos que si llega a la tienda está autenticado
        # En una app real, verificarías tokens o sesiones
        self.is_authenticated = True
        return rx.redirect("/tienda")

class LoginState(rx.State):
    email: str = ""
    password: str = ""
    error_msg: str = "Bienvenido"

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
            AuthState.is_authenticated = True
            return rx.redirect("/tienda")
        
        result = SUPABASE_SERVICE.login(self.email, self.password)
        if "success" in result:
            AuthState.is_authenticated = True
            return rx.redirect("/tienda")
        else:
            self.error_msg = "❌ Correo o contraseña incorrectos."

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

        result = SUPABASE_SERVICE.signup(self.email, self.password, self.birthdate, self.location)
        if "success" in result:
            return rx.redirect("/")
        else:
            self.error_msg = f"❌ {result.get('error', 'Error al crear cuenta')}"

class TiendaState(rx.State):
    mobos_amd: list[Producto] = []
    mobos_intel: list[Producto] = []
    cpus_amd: list[Producto] = []
    cpus_intel: list[Producto] = []
    
    search_query: str = ""
    selected_category: str = "todos"
    search_results: list[Producto] = []
    is_searching: bool = False
    
    cart_items: list[CartItem] = []
    show_cart: bool = False
    is_loading: bool = False

    def on_mount(self):
        if not self.has_products:
            yield self.load_products()

    def load_products(self):
        self.is_loading = True
        if not supabase:
            print("Supabase no disponible")
            self.is_loading = False
            return
        try:
            # Cargar Motherboards AMD
            response = supabase.table("productos").select("*").eq("categoria", "mobo").eq("marca", "amd").execute()
            self.mobos_amd = [self._to_producto(p) for p in (response.data or [])]
            
            # Cargar Motherboards Intel
            response = supabase.table("productos").select("*").eq("categoria", "mobo").eq("marca", "intel").execute()
            self.mobos_intel = [self._to_producto(p) for p in (response.data or [])]
            
            # Cargar CPUs AMD
            response = supabase.table("productos").select("*").eq("categoria", "cpu").eq("marca", "amd").execute()
            self.cpus_amd = [self._to_producto(p) for p in (response.data or [])]
            
            # Cargar CPUs Intel
            response = supabase.table("productos").select("*").eq("categoria", "cpu").eq("marca", "intel").execute()
            self.cpus_intel = [self._to_producto(p) for p in (response.data or [])]
            
        except Exception as e:
            print(f"Error cargando productos: {e}")
        self.is_loading = False

    def _to_producto(self, p: dict) -> Producto:
        return Producto(
            id=str(p.get("id", "")), 
            nombre=str(p.get("nombre", "")),
            precio=float(p.get("precio", 0) or 0),
            imagen=str(p.get("imagen", "")),
            categoria=str(p.get("categoria", "")),
            marca=str(p.get("marca", "")),
            socket=str(p.get("socket", ""))
        )
        
    @rx.var
    def all_products(self) -> list[Producto]:
        return self.mobos_amd + self.mobos_intel + self.cpus_amd + self.cpus_intel

    @rx.var
    def display_products(self) -> list[Producto]:
        if self.is_searching:
            return self.search_results
        else:
            return self.all_products

    def set_category_on_mount(self, category: str):
        """Método llamado por las páginas de categoría para aplicar el filtro."""
        # Asegurar que los productos estén cargados
        if not self.has_products:
            yield self.load_products()
        
        # Aplicar el filtro inmediatamente
        self.selected_category = category
        self.search_query = ""
        self.is_searching = True
        
        # Aplicar filtro basado en categoría
        if category == "mobo_amd":
            self.search_results = list(self.mobos_amd)
        elif category == "mobo_intel":
            self.search_results = list(self.mobos_intel)
        elif category == "cpu_amd":
            self.search_results = list(self.cpus_amd)
        elif category == "cpu_intel":
            self.search_results = list(self.cpus_intel)
        else:
            self.search_results = list(self.all_products)

    def set_search(self, query: str):
        self.search_query = query
        
        if query.strip():
            self.is_searching = True
            self.selected_category = "todos"
            self.apply_search()
        else:
            self.is_searching = False
            self.search_results = []

    def apply_search(self):
        query_lower = self.search_query.lower().strip()
        self.search_results = [p for p in self.all_products if query_lower in p.nombre.lower()]

    def clear_filters(self):
        self.search_query = ""
        self.selected_category = "todos"
        self.is_searching = False
        self.search_results = []

    # Métodos de Carrito
    def add_to_cart(self, product: Producto):
        for item in self.cart_items:
            if item.id == product.id:
                item.cantidad += 1
                self.cart_items = self.cart_items.copy()
                return
        new_item = CartItem(
            id=product.id,
            nombre=product.nombre,
            precio=product.precio,
            imagen=product.imagen,
            cantidad=1
        )
        self.cart_items.append(new_item)

    def remove_from_cart(self, product_id: str):
        self.cart_items = [item for item in self.cart_items if item.id != product_id]

    def increase_quantity(self, product_id: str):
        for item in self.cart_items:
            if item.id == product_id:
                item.cantidad += 1
                break
        self.cart_items = self.cart_items.copy()

    def decrease_quantity(self, product_id: str):
        for item in self.cart_items:
            if item.id == product_id:
                if item.cantidad > 1:
                    item.cantidad -= 1
                else:
                    self.remove_from_cart(product_id)
                    return
                break
        self.cart_items = self.cart_items.copy()

    def toggle_cart(self):
        self.show_cart = not self.show_cart

    def clear_cart(self):
        self.cart_items = []

    @rx.var
    def cart_total(self) -> float:
        total = 0.0
        for item in self.cart_items:
            total += item.precio * item.cantidad
        return round(total, 2)

    @rx.var
    def cart_count(self) -> int:
        return sum(item.cantidad for item in self.cart_items)
    
    @rx.var
    def has_products(self) -> bool:
        return len(self.all_products) > 0


# --- COMPONENTES UI ---

def animated_sphere(top, left, right, bottom, width, height, spin_duration, pulse_duration, delay):
    return rx.box(
        bg="radial-gradient(ellipse, #AA14F0 0%, rgba(170,20,240,0.0) 70%)",
        width=width, height=height, position="absolute",
        top=top, left=left, right=right, bottom=bottom,
        animation=f"float_and_grow {spin_duration} ease-in-out {delay} infinite alternate, pulse_color {pulse_duration} ease-in-out {delay} infinite",
        z_index=0,
    )

def product_card_tienda(product: Producto):
    return rx.box(
        rx.vstack(
            rx.image(
                src=rx.cond(product.imagen != "", product.imagen, "https://placehold.co/400x150/E8E8E8/333333?text=SIN+IMAGEN"),
                height="150px",
                width="100%",
                object_fit="contain",
                bg="#f0f0f0",
                border_radius="8px 8px 0 0",
            ),
            rx.vstack(
                rx.text(product.nombre, color="#333", weight="bold", size="3", no_of_lines=2),
                rx.hstack(
                    rx.badge(product.categoria.upper(), color_scheme="purple", size="1"),
                    rx.badge(product.marca.upper(), color_scheme="blue", size="1"),
                    spacing="2",
                ),
                rx.text("Socket: " + product.socket, color="gray", size="2"),
                rx.text("$" + product.precio.to_string(), color="#7c3aed", weight="bold", size="5"),
                spacing="2",
                align="start",
                width="100%",
                padding="10px",
            ),
            spacing="0",
            width="100%",
        ),
        rx.box(
            rx.button(
                rx.icon(tag="shopping-cart", size=16),
                size="1",
                bg="#7c3aed",
                color="white",
                border_radius="50%",
                padding="8px",
                on_click=lambda: TiendaState.add_to_cart(product),
                _hover={"bg": "#6d28d9", "transform": "scale(1.1)"},
            ),
            position="absolute",
            bottom="10px",
            right="10px",
        ),
        bg="white",
        border_radius="12px",
        padding="0 0 15px 0",
        position="relative",
        box_shadow="0 4px 15px rgba(0,0,0,0.1)",
        transition="all 0.3s ease",
        _hover={"transform": "translateY(-5px)", "box_shadow": "0 8px 25px rgba(0,0,0,0.2)"},
        overflow="hidden",
        min_width="250px",
        max_width="280px",
        flex_shrink="0",
    )

def cart_item(item: CartItem):
    return rx.hstack(
        rx.image(
            src=item.imagen,
            width="60px",
            height="60px",
            object_fit="contain",
            border_radius="8px",
            bg="#f0f0f0",
        ),
        rx.vstack(
            rx.text(item.nombre, color="white", size="2", weight="bold", no_of_lines=1),
            rx.text(f"${item.precio:.2f}", color="#a78bfa", size="2"),
            spacing="1",
            align="start",
            flex="1",
        ),
        rx.hstack(
            rx.button("-", size="1", variant="outline", color="white", on_click=lambda: TiendaState.decrease_quantity(item.id)),
            rx.text(item.cantidad, color="white", size="2", width="30px", text_align="center"),
            rx.button("+", size="1", variant="outline", color="white", on_click=lambda: TiendaState.increase_quantity(item.id)),
            spacing="1",
        ),
        rx.button(
            rx.icon(tag="trash-2", size=14),
            size="1",
            variant="ghost",
            color="red",
            on_click=lambda: TiendaState.remove_from_cart(item.id),
        ),
        width="100%",
        padding="10px",
        bg="rgba(255,255,255,0.1)",
        border_radius="8px",
        align="center",
    )

def cart_sidebar():
    return rx.cond(
        TiendaState.show_cart,
        rx.box(
            rx.box(
                on_click=TiendaState.toggle_cart,
                position="fixed",
                top="0", left="0", right="0", bottom="0",
                bg="rgba(0,0,0,0.5)",
                z_index=98,
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("Carrito de Compras", color="white", size="5", weight="bold"),
                        rx.spacer(),
                        rx.button(
                            rx.icon(tag="x", size=20),
                            variant="ghost",
                            color="white",
                            on_click=TiendaState.toggle_cart,
                        ),
                        width="100%",
                        padding="20px",
                        border_bottom="1px solid rgba(255,255,255,0.2)",
                    ),
                    rx.cond(
                        TiendaState.cart_count > 0,
                        rx.vstack(
                            rx.foreach(TiendaState.cart_items, cart_item),
                            spacing="3",
                            width="100%",
                            padding="20px",
                            overflow_y="auto",
                            flex="1",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.icon(tag="shopping-cart", size=50, color="gray"),
                                rx.text("Tu carrito está vacío", color="gray", size="3"),
                                spacing="3",
                                align="center",
                                justify="center",
                            ),
                            display="flex",
                            align_items="center",
                            justify_content="center",
                            width="100%",
                            flex="1",
                        ),
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text("Total:", color="white", size="4"),
                            rx.spacer(),
                            rx.text("$" + TiendaState.cart_total.to_string(), color="white", size="5", weight="bold"),
                            width="100%",
                        ),
                        rx.button(
                            "Proceder al Pago",
                            width="100%",
                            bg="linear-gradient(90deg, #7c3aed, #3b82f6)",
                            color="white",
                            size="3",
                            disabled=TiendaState.cart_count == 0,
                        ),
                        rx.button(
                            "Vaciar Carrito",
                            width="100%",
                            variant="outline",
                            color="white",
                            size="2",
                            on_click=TiendaState.clear_cart,
                            disabled=TiendaState.cart_count == 0,
                        ),
                        spacing="3",
                        width="100%",
                        padding="20px",
                        border_top="1px solid rgba(255,255,255,0.2)",
                    ),
                    height="100%",
                ),
                position="fixed",
                top="0",
                right="0",
                width="400px",
                height="100vh",
                bg="linear-gradient(135deg, #1e1b4b, #312e81)",
                z_index=99,
                box_shadow="-5px 0 25px rgba(0,0,0,0.3)",
            ),
        ),
        rx.box(),
    )

def product_section(title: str, product_list: rx.Var[list[Producto]]):
    return rx.vstack(
        rx.text(
            title, 
            size="6", 
            weight="bold", 
            color="white", 
            margin_top="50px", 
            align_self="flex-start",
            padding_left="20px"
        ),
        rx.cond(
            product_list.length() == 0,
            rx.text("No hay productos disponibles en esta categoría.", color="gray", size="4", padding_bottom="30px"),
            rx.grid(
                rx.foreach(product_list, product_card_tienda),
                columns="repeat(auto-fill, minmax(280px, 1fr))",
                gap="20px",
                width="100%",
                margin_top="15px",
            )
        ),
        width="100%",
        align="center",
    )

# NAVBAR
def navbar():
    return rx.hstack(
        rx.hstack(
            rx.image(src="logo.png", width="50px", height="50px", cursor="pointer", on_click=lambda: rx.redirect("/tienda")),
            rx.text("PC STORE", color="white", weight="bold", size="5", cursor="pointer", on_click=lambda: rx.redirect("/tienda")),
            spacing="2", align="center",
        ),
        rx.hstack(
            rx.button("Inicio", variant="ghost", color="white", on_click=lambda: rx.redirect("/tienda")),
            rx.button("Builder", variant="ghost", color="white", on_click=lambda: rx.redirect("/builder-select")),
            rx.menu.root(
                rx.menu.trigger(rx.button("Categorías", variant="ghost", color="white")),
                rx.menu.content(
                    rx.menu.item("Todos", on_click=lambda: rx.redirect("/tienda")), 
                    rx.menu.separator(),
                    rx.menu.item("── Motherboards ──", disabled=True),
                    rx.menu.item("Motherboards AMD", on_click=lambda: rx.redirect("/tienda/motherboardsamd")),
                    rx.menu.item("Motherboards Intel", on_click=lambda: rx.redirect("/tienda/motherboardsintel")),
                    rx.menu.separator(),
                    rx.menu.item("── Procesadores ──", disabled=True),
                    rx.menu.item("Procesadores AMD", on_click=lambda: rx.redirect("/tienda/procesadoresamd")),
                    rx.menu.item("Procesadores Intel", on_click=lambda: rx.redirect("/tienda/procesadoresintel")),
                ),
            ),
            spacing="2",
        ),
        rx.input(
            placeholder="Buscar productos...",
            value=TiendaState.search_query,
            on_change=TiendaState.set_search,
            bg="rgba(255,255,255,0.1)",
            color="white",
            border_radius="8px",
            width="250px",
            _placeholder={"color": "rgba(255,255,255,0.5)"}
        ),
        rx.spacer(),
        rx.box(
            rx.button(
                rx.icon(tag="shopping-cart", size=20),
                rx.cond(
                    TiendaState.cart_count > 0,
                    rx.badge(TiendaState.cart_count, color_scheme="red", variant="solid", margin_left="-8px", margin_top="-10px"),
                    rx.box()
                ),
                variant="ghost",
                color="white",
                on_click=TiendaState.toggle_cart,
            ),
        ),
        rx.button(
            rx.icon(tag="log-out", size=18),
            variant="ghost",
            color="white",
            on_click=lambda: rx.redirect("/"),
        ),
        width="100%",
        padding="15px 30px",
        bg="rgba(0, 0, 0, 0.5)",
        backdrop_filter="blur(10px)",
        position="sticky",
        top="0",
        z_index=50,
        align="center",
        spacing="4",
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

# --- PÁGINAS ---

def home():
    """Página de inicio que redirige al login"""
    return rx.box(
        rx.html(f"<style>{CSS_KEYFRAMES}</style>"),
        background_spheres(),
        rx.center(
            rx.vstack(
                rx.image(src="logo.png", width="200px", height="200px"),
                rx.text("PC STORE", size="9", weight="bold", color="white"),
                rx.text("Bienvenido a nuestra tienda", color="rgba(255,255,255,0.7)", size="5"),
                rx.button(
                    "Iniciar Sesión",
                    size="4",
                    bg="linear-gradient(90deg,#501794, #3E70A1)",
                    color="white",
                    border_radius="8px",
                    on_click=lambda: rx.redirect("/login"),
                    width="200px",
                    margin_top="30px"
                ),
                spacing="4",
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
                        value=LoginState.email,
                        on_change=LoginState.set_email,
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
                        value=LoginState.password,
                        on_change=LoginState.set_password,
                        bg="rgba(255,255,255,0.1)",
                        color="white",
                        padding="10px",
                        border_radius="8px",
                        width="100%",
                        _placeholder={"color": "rgba(255,255,255,0.5)"}
                    ),

                    rx.text(
                        LoginState.error_msg, 
                        color=rx.cond(
                            LoginState.error_msg.startswith("❌"), 
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
                        on_click=LoginState.login,
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
        
        on_mount=LoginState.on_mount,
        bg="linear-gradient(135deg, #120024, #29004A)",
        height="100vh", 
        width="100%",
        position="relative",
        overflow="hidden",
    )

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

        on_mount=CreateAccountState.on_mount,
        bg="linear-gradient(135deg, #120024, #29004A)",
        height="100vh", 
        width="100%",
        position="relative",
        overflow="hidden",
    )

def builder_select_page():
    return rx.box(
        rx.html(f"<style>{CSS_KEYFRAMES}</style>"),
        background_spheres(),
        navbar(),
        cart_sidebar(),
        rx.center(
            rx.vstack(
                rx.text("Armador de PC", size="9", weight="bold", color="white"),
                rx.text("Selecciona tu plataforma para comenzar:", color="rgba(255,255,255,0.7)", size="4"),
                rx.hstack(
                    chip_selector(
                        logo_url="https://cdn.worldvectorlogo.com/logos/amd-advanced-micro-devices-white.svg",
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
                    margin_top="30px",
                ),
                spacing="5",
                align="center",
                padding="20px",
                z_index=1
            ),
            height="calc(100vh - 80px)",
            width="100%",
        ),
        bg="linear-gradient(135deg, #120024, #29004A)",
        min_height="100vh",
        width="100%",
        position="relative",
        overflow="hidden",
    )

def tienda_content_view():
    return rx.center(
        rx.cond(
            TiendaState.is_loading,
            rx.vstack(
                rx.spinner(size="3", color="white"), 
                rx.text("Cargando productos...", color="white"),
                margin_top="100px"
            ),
            rx.vstack(
                rx.text(
                    rx.cond(
                        TiendaState.is_searching,
                        f"Resultados para Categoría: {TiendaState.selected_category.upper()}",
                        "Tienda Principal"
                    ), 
                    size="7", weight="bold", color="white", margin_top="20px"
                ),
                rx.cond(
                    TiendaState.is_searching,
                    rx.vstack(
                        rx.cond(
                            TiendaState.display_products.length() == 0,
                            rx.text("No se encontraron productos en esta categoría.", color="gray", size="4"),
                            rx.grid(
                                rx.foreach(TiendaState.display_products, product_card_tienda),
                                columns="repeat(auto-fill, minmax(280px, 1fr))", 
                                gap="20px", 
                                width="100%",
                                margin_top="30px",
                            )
                        ),
                        rx.button("Limpiar Filtros", variant="outline", color="white", margin_top="40px", on_click=lambda: rx.redirect("/tienda")),
                        width="100%",
                    ),
                    rx.vstack(
                        product_section("Productos Destacados", TiendaState.all_products[:4]),
                        product_section("Motherboards Intel", TiendaState.mobos_intel),
                        product_section("Motherboards AMD", TiendaState.mobos_amd),
                        product_section("Procesadores Intel", TiendaState.cpus_intel),
                        product_section("Procesadores AMD", TiendaState.cpus_amd),
                        width="100%",
                        padding_bottom="50px",
                    )
                ),
                width="90%",
                max_width="1200px",
                align="center",
                padding_bottom="50px",
                z_index=1,
            ),
        ),
        width="100%",
        min_height="calc(100vh - 80px)",
    )

def tienda_page():
    return rx.box(
        rx.html(f"<style>{CSS_KEYFRAMES}</style>"),
        background_spheres(),
        navbar(),
        cart_sidebar(),
        tienda_content_view(),
        on_mount=TiendaState.on_mount,
        bg="linear-gradient(135deg, #120024, #29004A)",
        min_height="100vh",
        width="100%",
        position="relative",
        overflow="hidden",
    )

def category_page_template(category_key: str):
    return rx.box(
        rx.html(f"<style>{CSS_KEYFRAMES}</style>"),
        background_spheres(),
        navbar(),
        cart_sidebar(),
        tienda_content_view(),
        on_mount=lambda: TiendaState.set_category_on_mount(category_key),
        bg="linear-gradient(135deg, #120024, #29004A)",
        min_height="100vh",
        width="100%",
        position="relative",
        overflow="hidden",
    )

def motherboards_amd_page():
    return category_page_template("mobo_amd")

def motherboards_intel_page():
    return category_page_template("mobo_intel")

def procesadores_amd_page():
    return category_page_template("cpu_amd")

def procesadores_intel_page():
    return category_page_template("cpu_intel")

# --- APP ---
app = rx.App(
    style={
        "font_family": "Montserrat, sans-serif",
        "color": "white",
        "background_color": "#0a0a0a"
    }
)

# Configurar rutas principales
app.add_page(home, route="/")
app.add_page(login_page, route="/login")
app.add_page(create_account_page, route="/create-account")
app.add_page(tienda_page, route="/tienda")
app.add_page(motherboards_amd_page, route="/tienda/motherboardsamd")
app.add_page(motherboards_intel_page, route="/tienda/motherboardsintel")
app.add_page(procesadores_amd_page, route="/tienda/procesadoresamd")
app.add_page(procesadores_intel_page, route="/tienda/procesadoresintel")
app.add_page(builder_select_page, route="/builder-select")
app.add_page(builder.builder_page, route="/builder/amd")
app.add_page(builder.builder_page, route="/builder/intel")