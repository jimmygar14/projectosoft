import reflex as rx
import os
from supabase import create_client, Client

# --- Configuración de Supabase ---
# NOTA: En un entorno real, las variables de entorno deben estar en la configuración de Reflex, no aquí.
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://arcwophrnygdpiouboli.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_4Qkr8vJXHFiVHmiaUIynVw_yy6_bRXR")

# Inicialización del cliente de Supabase
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None
    print(f"Error al conectar a Supabase: {e}")

# --- Constantes de Estilo Dinámico ---
# Definimos los colores base para Intel (Azul) y AMD (Verde)
INTEL_COLOR = "#007bff"  # Azul fuerte
INTEL_LIGHT = "#63b3ed" # Azul claro
AMD_COLOR = "#10b981"    # Verde fuerte
AMD_LIGHT = "#6ee7b7"  # Verde claro

# Colores del fondo principal
DARK_BG_GRADIENT = "linear-gradient(135deg, #120024, #29004A)" # Degradado oscuro (Morado a Azul oscuro)
PRIMARY_ACCENT_COLOR = "#a400ff" # Color para burbujas, etc.

class BuilderState(rx.State):
    """Estado para manejar la lógica del armado de PC."""
    chosen_platform: str = "" # 'amd' o 'intel'
    
    # Listas de productos cargados desde la DB
    mobos: list[dict] = []
    cpus: list[dict] = []
    
    # Selecciones del usuario
    selected_mobo: dict = {}
    selected_cpu: dict = {}
    
    # Control de precio
    total_price: float = 0.0

    @rx.var
    def target_socket(self) -> str:
        """Calcula el socket objetivo basado en la plataforma elegida."""
        return "am5" if self.chosen_platform == "amd" else "lga1700"

    @rx.var
    def accent_color(self) -> str:
        """Devuelve el color de acento principal (Azul para Intel, Verde para AMD)."""
        return AMD_COLOR if self.chosen_platform == "amd" else INTEL_COLOR

    @rx.var
    def accent_light_color(self) -> str:
        """Devuelve el color de acento claro (para bordes seleccionados)."""
        return AMD_LIGHT if self.chosen_platform == "amd" else INTEL_LIGHT


    def fetch_components(self):
        """Busca y actualiza los componentes desde Supabase y establece la plataforma."""
        platform_param = self.router.page.params.get("platform", "")
        
        if not platform_param:
            return 
            
        self.chosen_platform = platform_param.lower()

        self.reset_selections() 
        
        if not supabase: 
            print("No se puede conectar a Supabase, mostrando listas vacías.")
            return

        # 1. Traer MOBOs
        try:
            # Ahora traemos todos los sockets Intel si la plataforma es intel
            if self.chosen_platform == "intel":
                response_mobo = supabase.table("productos").select("*").eq("categoria", "mobo").eq("marca", "intel").execute()
            else: # AMD
                 response_mobo = supabase.table("productos").select("*").eq("categoria", "mobo").eq("marca", "amd").execute()
                
            self.mobos = response_mobo.data
        except Exception as e:
            print(f"Error al cargar MOBOs: {e}")
            self.mobos = []

        # 2. Traer CPUs
        try:
            response_cpu = supabase.table("productos").select("*").eq("categoria", "cpu").eq("marca", self.chosen_platform).execute()
            self.cpus = response_cpu.data
        except Exception as e:
            print(f"Error al cargar CPUs: {e}")
            self.cpus = []
            
        print(f"Cargados {len(self.mobos)} MOBOs y {len(self.cpus)} CPUs para {self.chosen_platform.upper()}")

    # --- Lógica de Selección/Deselección ---
    
    def select_mobo(self, mobo: dict):
        """Selecciona o deselecciona Motherboard."""
        if self.selected_mobo.get("id") == mobo.get("id"):
            self.selected_mobo = {} 
            self.selected_cpu = {} 
        else:
            self.selected_mobo = mobo 
            
            # Al cambiar la MOBO, re-evaluamos la compatibilidad del CPU
            if self.selected_cpu:
                cpu_socket = self.selected_cpu.get("socket")
                mobo_socket = mobo.get("socket")
                cpu_nombre = self.selected_cpu.get("nombre")
                mobo_nombre = mobo.get("nombre")

                # Lógica de la excepción: Si se cumple la excepción especial
                is_exception = cpu_nombre == "Intel Core i7-10700K" and mobo_nombre == "MSI MAG B760 TOMAHAWK WIFI"
                
                # Si el socket no coincide Y NO es el caso de excepción, deseleccionar CPU
                if cpu_socket != mobo_socket and not is_exception:
                    self.selected_cpu = {}
        self.calculate_total()

    def select_cpu(self, cpu: dict):
        """Selecciona o deselecciona CPU."""
        if self.selected_cpu.get("id") == cpu.get("id"):
            self.selected_cpu = {} 
        else:
            if not self.selected_mobo:
                return 
            
            # Variables para la compatibilidad
            cpu_socket = cpu.get("socket")
            mobo_socket = self.selected_mobo.get("socket")
            cpu_nombre = cpu.get("nombre")
            mobo_nombre = self.selected_mobo.get("nombre")

            # Lógica de la excepción: Si se cumple la excepción especial
            is_exception = cpu_nombre == "Intel Core i7-10700K" and mobo_nombre == "MSI MAG B760 TOMAHAWK WIFI"
            
            # El CPU solo se selecciona si el socket coincide O si es el caso de excepción
            if cpu_socket == mobo_socket or is_exception:
                self.selected_cpu = cpu 
            else:
                # Si es incompatible y no es la excepción, no hacemos nada o mostramos un error
                print(f"Incompatible: CPU {cpu_socket} vs MOBO {mobo_socket}")
                return # No selecciona el CPU
                
        self.calculate_total()
        
    def reset_selections(self):
        """Resetea todas las selecciones y el total."""
        self.selected_mobo = {}
        self.selected_cpu = {}
        self.total_price = 0.0
        
    def calculate_total(self):
        """Calcula el precio total de los componentes seleccionados."""
        price = 0.0
        if self.selected_mobo: 
            price += float(self.selected_mobo.get('precio', 0) or 0)
        if self.selected_cpu: 
            price += float(self.selected_cpu.get('precio', 0) or 0)
        self.total_price = round(price, 2)


def product_card(product: dict, type: str):
    """Tarjeta de producto con lógica de selección y compatibilidad visual."""
    
    # --- Estilos Fijos ---
    BG_CARD = "white"
    TEXT_COLOR = "#333333" # Color oscuro para el texto sobre fondo blanco
    
    # 1. ¿Está seleccionado?
    is_selected = rx.cond(
        type == "mobo",
        BuilderState.selected_mobo.get("id") == product["id"],
        BuilderState.selected_cpu.get("id") == product["id"]
    )
    
    # 2. ¿Es compatible? (Compatibilidad de socket + Excepción)
    
    # --- LÓGICA DE EXCEPCIÓN: MSI B760 TOMAHAWK (lga1700) y Core i7-10700K (lga1200) ---
    # Variable: ¿El CPU actual en el bucle es el Intel Core i7-10700K?
    is_10700k = product.get("nombre") == "Intel Core i7-10700K"
    # Variable: ¿La MOBO seleccionada es la MSI MAG B760 TOMAHAWK WIFI?
    is_b760_tomahawk_selected = BuilderState.selected_mobo.get("nombre") == "MSI MAG B760 TOMAHAWK WIFI"
    
    # La excepción es True si el producto actual es el 10700K Y la MOBO seleccionada es la TOMAHAWK.
    is_exception_case = is_10700k & is_b760_tomahawk_selected

    # Compatibilidad base: El socket del producto (CPU) debe coincidir con el socket de la MOBO seleccionada.
    socket_match = product.get("socket") == BuilderState.selected_mobo.get("socket")
    
    # La compatibilidad final es si hay coincidencia de socket O si se cumple la excepción.
    is_compatible = rx.cond(
        type == "mobo",
        True, # MOBO siempre es compatible en su propia lista
        socket_match | is_exception_case
    )
    # --- FIN LÓGICA DE EXCEPCIÓN ---
    
    # --- Lógica Condicional Reflex (Client-Side) ---
    no_mobo_selected = BuilderState.selected_mobo.get("socket") == None

    if type == "cpu":
        # Deshabilitado si: 1. No hay MOBO O 2. Es incompatible
        is_disabled_var = no_mobo_selected | (~is_compatible) 

        # Texto del socket
        socket_text_var = rx.cond(
            no_mobo_selected,
            "⚠️ Selecciona Placa Madre",
            rx.cond(
                ~is_compatible, 
                "❌ Socket Incompatible", 
                rx.cond(
                    is_exception_case, # Mostrar mensaje especial si es la excepción
                    "✅ Excepción de BIOS (LGA1200)",
                    f"Socket: {product.get('socket', 'N/A')}"
                )
            )
        )
        
        # Color del texto del socket
        socket_color_var = rx.cond(
            no_mobo_selected,
            "orange", # Advertencia de no MOBO
            rx.cond(
                ~is_compatible, 
                "red", 
                BuilderState.accent_color
            ) # Incompatible o OK
        )
        
        # Opacidad y eventos de puntero
        opacity_var = rx.cond(is_disabled_var, "0.5", "1")
        pointer_events_var = rx.cond(is_disabled_var, "none", "auto")

    else: # type == "mobo"
        is_disabled_var = False
        socket_text_var = f"Socket: {product.get('socket', 'N/A')}"
        socket_color_var = BuilderState.accent_color
        opacity_var = "1"
        pointer_events_var = "auto"

    PRICE_TEXT = rx.text(
        f"${product.get('precio', '0.00'):.2f}", 
        color=BuilderState.accent_color, 
        weight="bold", 
        size="4"
    )
    
    # --- Estilo de Borde Dinámico ---
    dynamic_border = rx.cond(
        ~is_compatible, 
        "2px solid red", # Incompatible: borde rojo
        rx.cond(
            is_selected, 
            rx.color_mode_cond(
                light=f"3px solid {BuilderState.accent_color}", # Color principal fuerte si seleccionado
                dark=f"3px solid {BuilderState.accent_light_color}"
            ), 
            "1px solid #ddd" # Normal: borde gris
        )
    )

    return rx.box(
        rx.vstack(
            rx.image(
                src=product.get("imagen", "https://placehold.co/400x120/E8E8E8/333333?text=SIN+IMAGEN"), 
                height="120px", 
                width="100%", 
                object_fit="contain", 
                bg="#f0f0f0", 
                border_radius="6px"
            ),
            rx.text(product.get("nombre", "Producto sin nombre"), color=TEXT_COLOR, weight="bold", size="3", no_of_lines=2, margin_top="10px"),
            
            # Etiqueta de socket y compatibilidad
            rx.text(
                socket_text_var, 
                color=socket_color_var, 
                size="2"
            ),
            
            rx.hstack(
                PRICE_TEXT,
                rx.spacer(),
                rx.button(
                    rx.cond(is_selected, "Deseleccionar", "Seleccionar"),
                    size="2",
                    disabled=rx.cond(type == "cpu", is_disabled_var, False), 
                    bg=rx.cond(
                        is_disabled_var, 
                        "#cccccc", 
                        BuilderState.accent_color # Color del botón usando el acento dinámico
                    ),
                    color=rx.cond(is_selected, BG_CARD, "white"),
                    on_click=lambda: rx.cond(
                        type == "mobo",
                        BuilderState.select_mobo(product),
                        BuilderState.select_cpu(product)
                    )
                ),
                width="100%",
                margin_top="10px"
            ),
            padding="15px",
            spacing="2"
        ),
        bg=BG_CARD, 
        # Borde dinámico
        border=dynamic_border,
        opacity=opacity_var,
        pointer_events=pointer_events_var, 
        border_radius="12px",
        width="100%",
        box_shadow="0 4px 10px rgba(0, 0, 0, 0.1)",
        transition="all 0.3s ease-in-out",
        _hover={
            "transform": "translateY(-5px)", 
            "boxShadow": rx.cond(is_disabled_var, "0 4px 10px rgba(0, 0, 0, 0.1)", "0 8px 15px rgba(0, 0, 0, 0.3)")
        }
    )

@rx.page(route="/builder/[platform]", on_load=BuilderState.fetch_components) 
def builder_page():
    # --- ESTILOS DE FONDO PRINCIPAL SOLICITADOS ---
    BACKGROUND_STYLE = {
        # Degradado oscuro de la página principal
        "background": DARK_BG_GRADIENT, 
        "min_height": "100vh",
        "width": "100%",
        "position": "relative",
        "overflow": "hidden"
    }
    
    # Estilos BASE para las "burbujas" flotantes
    BUBBLE_STYLE = {
        "position": "absolute",
        "border_radius": "50%",
        "filter": "blur(50px)", # Aumentamos el desenfoque para un efecto más suave
        "animation": "float 20s ease-in-out infinite", # Animación más lenta
        "z_index": "0" # Asegura que las burbujas estén detrás del contenido
    }
    
    platform_name = rx.cond(
        BuilderState.chosen_platform != "",
        rx.text(f"ARMADOR PC {BuilderState.chosen_platform.upper()}", color="#fff"), # Texto en blanco
        rx.text("ARMADOR PC PERSONALIZADO", color="#fff")
    )
    
    return rx.box(
        # Contenedor principal con el fondo de la página principal
        rx.box(
            # Simulación de burbujas flotantes (Definición individual de bg y opacity)
            # Burbuja 1: Morado
            rx.box(**BUBBLE_STYLE, width="250px", height="250px", top="10%", left="5%", opacity="0.4", bg=PRIMARY_ACCENT_COLOR, style={"filter": "blur(80px)"}),
            
            # Burbuja 2: Morado
            rx.box(**BUBBLE_STYLE, width="150px", height="150px", bottom="5%", right="15%", opacity="0.4", bg=PRIMARY_ACCENT_COLOR),
            
            # Burbuja 3: Fondo azul diferente (#3E70A1)
            rx.box(**BUBBLE_STYLE, width="300px", height="300px", top="50%", left="70%", opacity="0.2", bg="#3E70A1"), 
            
            rx.center(
                rx.vstack(
                    # --- HEADER ---
                    rx.hstack(
                        rx.button(
                            "← Volver", 
                            on_click=lambda: rx.redirect("/"), 
                            variant="ghost", 
                            color="white", # Texto blanco
                            size="3", 
                            _hover={"color": BuilderState.accent_light_color, "bg": "rgba(255, 255, 255, 0.1)"}
                        ),
                        
                        # Título dinámico
                        rx.heading(
                            platform_name,
                            size="8",
                            color="white",
                            style={"fontFamily": "Inter, sans-serif"}
                        ),
                        rx.spacer(),
                        
                        rx.box(
                            rx.text("Total Estimado:", color="whiteAlpha.700", size="2"),
                            rx.text(f"${BuilderState.total_price:.2f}", color="white", weight="bold", size="6"),
                            text_align="right",
                            margin_left="20px"
                        ),
                        
                        # Botón con el estilo corregido
                        rx.button(
                            "Actualizar Productos",
                            on_click=BuilderState.fetch_components,
                            color_scheme="gray", 
                            variant="outline",
                            size="2",
                            border="1px solid white",
                            color="white",
                            _hover={"bg": "rgba(255, 255, 255, 0.2)"}
                        ),
                        
                        width="100%",
                        padding="20px",
                        align="center",
                        bg="rgba(0, 0, 0, 0.3)", # Header semi-transparente
                        border_bottom="1px solid rgba(255, 255, 255, 0.2)",
                        position="sticky", 
                        top="0",
                        z_index="10"
                    ),
                    
                    # --- CONTENIDO PRINCIPAL: TRANSPARENTE ---
                    rx.box(
                        # SECCIÓN 1: MOTHERBOARD
                        rx.box(
                            # Títulos en blanco para que se vean sobre el fondo oscuro
                            rx.text("1. Selecciona tu Placa Madre", color="white", size="6", weight="bold", margin_bottom="20px"),
                            rx.text(f"Socket Requerido para la plataforma {BuilderState.chosen_platform.upper()}: {BuilderState.target_socket.upper()}", color="gray.300", size="3", margin_bottom="15px"),
                            rx.grid(
                                rx.foreach(
                                    BuilderState.mobos,
                                    lambda p: product_card(p, "mobo")
                                ),
                                columns={"initial": "1", "sm": "2", "md": "3", "lg": "4"},
                                spacing="6",
                                width="100%"
                            ),
                            width="100%",
                            padding="20px"
                        ),

                        # SECCIÓN 2: PROCESADOR
                        rx.box(
                            # Títulos en blanco para que se vean sobre el fondo oscuro
                            rx.text("2. Selecciona tu Procesador", color="white", size="6", weight="bold", margin_bottom="20px", padding_top="40px"),
                            rx.cond(
                                BuilderState.selected_mobo,
                                rx.text(f"Placa Madre Seleccionada: {BuilderState.selected_mobo.get('nombre')}. Buscando CPUs compatibles con Socket: {BuilderState.selected_mobo.get('socket')}", color=BuilderState.accent_light_color, size="3", weight="bold", margin_bottom="15px"),
                                rx.text("⚠️ Debes seleccionar una Placa Madre (paso 1) antes de seleccionar un Procesador.", color="red", size="3", weight="bold", margin_bottom="15px")
                            ),
                            rx.box(
                                rx.grid(
                                    rx.foreach(
                                        BuilderState.cpus,
                                        lambda p: product_card(p, "cpu")
                                    ),
                                    columns={"initial": "1", "sm": "2", "md": "3", "lg": "4"},
                                    spacing="6",
                                    width="100%"
                                ),
                                opacity=rx.cond(BuilderState.selected_mobo, "1", "0.5"), 
                                pointer_events=rx.cond(BuilderState.selected_mobo, "auto", "none"),
                                width="100%"
                            ),
                            width="100%",
                            padding="20px"
                        ),
                        
                        # Fondo es transparente
                        bg="transparent", 
                        border_radius="15px",
                        margin_top="20px",
                        margin_bottom="40px"
                    ),

                    width="100%",
                    max_width="1200px",
                ),
                width="100%",
                padding_bottom="50px",
                z_index="1" # Asegura que el contenido esté sobre las burbujas
            ),
            style=BACKGROUND_STYLE # Aplicamos el estilo de fondo oscuro
        )
    )