import reflex as rx
import os
from supabase import create_client, Client

# --- Configuración de Supabase ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://arcwophrnygdpiouboli.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_publishable_4Qkr8vJXHFiVHmiaUIynVw_yy6_bRXR")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    supabase = None
    print(f"Error al conectar a Supabase: {e}")

# --- Constantes de Estilo ---
INTEL_COLOR = "#007bff"
INTEL_LIGHT = "#63b3ed"
AMD_COLOR = "#10b981"
AMD_LIGHT = "#6ee7b7"
DARK_BG_GRADIENT = "linear-gradient(135deg, #120024, #29004A)"
PRIMARY_ACCENT_COLOR = "#a400ff"


class BuilderState(rx.State):
    """Estado para manejar la lógica del armado de PC."""
    chosen_platform: str = ""
    mobos: list[dict] = []
    cpus: list[dict] = []
    selected_mobo: dict = {}
    selected_cpu: dict = {}
    total_price: float = 0.0

    @rx.var
    def target_socket(self) -> str:
        return "am5" if self.chosen_platform == "amd" else "lga1700"

    @rx.var
    def accent_color(self) -> str:
        return AMD_COLOR if self.chosen_platform == "amd" else INTEL_COLOR

    @rx.var
    def accent_light_color(self) -> str:
        return AMD_LIGHT if self.chosen_platform == "amd" else INTEL_LIGHT

    def fetch_components(self):
        """Busca y actualiza los componentes desde Supabase."""
        # Obtener plataforma de la URL
        try:
            platform_param = self.router.page.params.get("platform", "")
            if not platform_param:
                current_path = self.router.page.path
                if "/builder/" in current_path:
                    platform_param = current_path.split("/builder/")[-1].strip("/")
        except Exception as e:
            print(f"Error obteniendo plataforma: {e}")
            platform_param = ""

        print(f"Platform detectada: '{platform_param}'")

        if not platform_param:
            return

        self.chosen_platform = platform_param.lower()
        self.reset_selections()

        if not supabase:
            print("Supabase no disponible")
            return

        # Cargar MOBOs
        try:
            if self.chosen_platform == "intel":
                response = supabase.table("productos").select("*").eq("categoria", "mobo").eq("marca", "intel").execute()
            else:
                response = supabase.table("productos").select("*").eq("categoria", "mobo").eq("marca", "amd").execute()
            self.mobos = response.data or []
            print(f"MOBOs cargadas: {len(self.mobos)}")
        except Exception as e:
            print(f"Error cargando MOBOs: {e}")
            self.mobos = []

        # Cargar CPUs
        try:
            response = supabase.table("productos").select("*").eq("categoria", "cpu").eq("marca", self.chosen_platform).execute()
            self.cpus = response.data or []
            print(f"CPUs cargados: {len(self.cpus)}")
        except Exception as e:
            print(f"Error cargando CPUs: {e}")
            self.cpus = []

    def select_mobo(self, mobo: dict):
        if self.selected_mobo.get("id") == mobo.get("id"):
            self.selected_mobo = {}
            self.selected_cpu = {}
        else:
            self.selected_mobo = mobo
            if self.selected_cpu:
                cpu_socket = self.selected_cpu.get("socket")
                mobo_socket = mobo.get("socket")
                cpu_nombre = self.selected_cpu.get("nombre")
                mobo_nombre = mobo.get("nombre")
                is_exception = cpu_nombre == "Intel Core i7-10700K" and mobo_nombre == "MSI MAG B760 TOMAHAWK WIFI"
                if cpu_socket != mobo_socket and not is_exception:
                    self.selected_cpu = {}
        self.calculate_total()

    def select_cpu(self, cpu: dict):
        if self.selected_cpu.get("id") == cpu.get("id"):
            self.selected_cpu = {}
        else:
            if not self.selected_mobo:
                return
            cpu_socket = cpu.get("socket")
            mobo_socket = self.selected_mobo.get("socket")
            cpu_nombre = cpu.get("nombre")
            mobo_nombre = self.selected_mobo.get("nombre")
            is_exception = cpu_nombre == "Intel Core i7-10700K" and mobo_nombre == "MSI MAG B760 TOMAHAWK WIFI"
            if cpu_socket == mobo_socket or is_exception:
                self.selected_cpu = cpu
            else:
                print(f"Incompatible: CPU {cpu_socket} vs MOBO {mobo_socket}")
                return
        self.calculate_total()

    def reset_selections(self):
        self.selected_mobo = {}
        self.selected_cpu = {}
        self.total_price = 0.0

    def calculate_total(self):
        price = 0.0
        if self.selected_mobo:
            price += float(self.selected_mobo.get('precio', 0) or 0)
        if self.selected_cpu:
            price += float(self.selected_cpu.get('precio', 0) or 0)
        self.total_price = round(price, 2)


def product_card(product: dict, type: str):
    BG_CARD = "white"
    TEXT_COLOR = "#333333"

    is_selected = rx.cond(
        type == "mobo",
        BuilderState.selected_mobo.get("id") == product["id"],
        BuilderState.selected_cpu.get("id") == product["id"]
    )

    is_10700k = product.get("nombre") == "Intel Core i7-10700K"
    is_b760_tomahawk_selected = BuilderState.selected_mobo.get("nombre") == "MSI MAG B760 TOMAHAWK WIFI"
    is_exception_case = is_10700k & is_b760_tomahawk_selected
    socket_match = product.get("socket") == BuilderState.selected_mobo.get("socket")
    is_compatible = rx.cond(type == "mobo", True, socket_match | is_exception_case)

    no_mobo_selected = BuilderState.selected_mobo.get("socket") == None

    if type == "cpu":
        is_disabled_var = no_mobo_selected | (~is_compatible)
        socket_text_var = rx.cond(
            no_mobo_selected,
            "⚠️ Selecciona Placa Madre",
            rx.cond(
                ~is_compatible,
                "❌ Socket Incompatible",
                rx.cond(is_exception_case, "✅ Excepción de BIOS (LGA1200)", f"Socket: {product.get('socket', 'N/A')}")
            )
        )
        socket_color_var = rx.cond(no_mobo_selected, "orange", rx.cond(~is_compatible, "red", BuilderState.accent_color))
        opacity_var = rx.cond(is_disabled_var, "0.5", "1")
        pointer_events_var = rx.cond(is_disabled_var, "none", "auto")
    else:
        is_disabled_var = False
        socket_text_var = f"Socket: {product.get('socket', 'N/A')}"
        socket_color_var = BuilderState.accent_color
        opacity_var = "1"
        pointer_events_var = "auto"

    PRICE_TEXT = rx.text(f"${product.get('precio', '0.00'):.2f}", color=BuilderState.accent_color, weight="bold", size="4")

    dynamic_border = rx.cond(
        ~is_compatible,
        "2px solid red",
        rx.cond(is_selected, f"3px solid {BuilderState.accent_color}", "1px solid #ddd")
    )

    return rx.box(
        rx.vstack(
            rx.image(
                src=product.get("imagen", "https://placehold.co/400x120/E8E8E8/333333?text=SIN+IMAGEN"),
                height="120px", width="100%", object_fit="contain", bg="#f0f0f0", border_radius="6px"
            ),
            rx.text(product.get("nombre", "Producto sin nombre"), color=TEXT_COLOR, weight="bold", size="3", no_of_lines=2, margin_top="10px"),
            rx.text(socket_text_var, color=socket_color_var, size="2"),
            rx.hstack(
                PRICE_TEXT,
                rx.spacer(),
                rx.button(
                    rx.cond(is_selected, "Deseleccionar", "Seleccionar"),
                    size="2",
                    disabled=rx.cond(type == "cpu", is_disabled_var, False),
                    bg=rx.cond(is_disabled_var, "#cccccc", BuilderState.accent_color),
                    color=rx.cond(is_selected, BG_CARD, "white"),
                    on_click=lambda: rx.cond(type == "mobo", BuilderState.select_mobo(product), BuilderState.select_cpu(product))
                ),
                width="100%", margin_top="10px"
            ),
            padding="15px", spacing="2"
        ),
        bg=BG_CARD,
        border=dynamic_border,
        opacity=opacity_var,
        pointer_events=pointer_events_var,
        border_radius="12px",
        width="100%",
        box_shadow="0 4px 10px rgba(0, 0, 0, 0.1)",
        transition="all 0.3s ease-in-out",
        _hover={"transform": "translateY(-5px)", "boxShadow": rx.cond(is_disabled_var, "0 4px 10px rgba(0, 0, 0, 0.1)", "0 8px 15px rgba(0, 0, 0, 0.3)")}
    )


def builder_page():
    """Página del builder - SIN decorador @rx.page"""
    BACKGROUND_STYLE = {
        "background": DARK_BG_GRADIENT,
        "min_height": "100vh",
        "width": "100%",
        "position": "relative",
        "overflow": "hidden"
    }

    BUBBLE_STYLE = {
        "position": "absolute",
        "border_radius": "50%",
        "filter": "blur(50px)",
        "z_index": "0"
    }

    platform_name = rx.cond(
        BuilderState.chosen_platform != "",
        rx.text(f"ARMADOR PC {BuilderState.chosen_platform.upper()}", color="#fff"),
        rx.text("ARMADOR PC PERSONALIZADO", color="#fff")
    )

    return rx.box(
        rx.box(
            rx.box(**BUBBLE_STYLE, width="250px", height="250px", top="10%", left="5%", opacity="0.4", bg=PRIMARY_ACCENT_COLOR, style={"filter": "blur(80px)"}),
            rx.box(**BUBBLE_STYLE, width="150px", height="150px", bottom="5%", right="15%", opacity="0.4", bg=PRIMARY_ACCENT_COLOR),
            rx.box(**BUBBLE_STYLE, width="300px", height="300px", top="50%", left="70%", opacity="0.2", bg="#3E70A1"),

            rx.center(
                rx.vstack(
                    rx.hstack(
                        rx.button("← Volver", on_click=lambda: rx.redirect("/builder-select"), variant="ghost", color="white", size="3"),
                        rx.heading(platform_name, size="8", color="white"),
                        rx.spacer(),
                        rx.box(
                            rx.text("Total Estimado:", color="whiteAlpha.700", size="2"),
                            rx.text(f"${BuilderState.total_price:.2f}", color="white", weight="bold", size="6"),
                            text_align="right", margin_left="20px"
                        ),
                        rx.button("Reiniciar", on_click=BuilderState.fetch_components, variant="outline", size="2", border="1px solid white", color="white"),
                        width="100%", padding="20px", align="center", bg="rgba(0, 0, 0, 0.3)", border_bottom="1px solid rgba(255, 255, 255, 0.2)", position="sticky", top="0", z_index="10"
                    ),

                    rx.box(
                        rx.box(
                            rx.text("1. Selecciona tu Placa Madre", color="white", size="6", weight="bold", margin_bottom="20px"),
                            rx.grid(rx.foreach(BuilderState.mobos, lambda p: product_card(p, "mobo")), columns={"initial": "1", "sm": "2", "md": "3", "lg": "4"}, spacing="6", width="100%"),
                            width="100%", padding="20px"
                        ),
                        rx.box(
                            rx.text("2. Selecciona tu Procesador", color="white", size="6", weight="bold", margin_bottom="20px", padding_top="40px"),
                            rx.cond(
                                BuilderState.selected_mobo,
                                rx.text(f"Placa seleccionada: {BuilderState.selected_mobo.get('nombre')}", color=BuilderState.accent_light_color, size="3", weight="bold", margin_bottom="15px"),
                                rx.text("⚠️ Selecciona una Placa Madre primero", color="red", size="3", weight="bold", margin_bottom="15px")
                            ),
                            rx.box(
                                rx.grid(rx.foreach(BuilderState.cpus, lambda p: product_card(p, "cpu")), columns={"initial": "1", "sm": "2", "md": "3", "lg": "4"}, spacing="6", width="100%"),
                                opacity=rx.cond(BuilderState.selected_mobo, "1", "0.5"),
                                pointer_events=rx.cond(BuilderState.selected_mobo, "auto", "none"),
                                width="100%"
                            ),
                            width="100%", padding="20px"
                        ),
                        bg="transparent", border_radius="15px", margin_top="20px", margin_bottom="40px"
                    ),
                    width="100%", max_width="1200px",
                ),
                width="100%", padding_bottom="50px", z_index="1"
            ),
            style=BACKGROUND_STYLE
        ),
        on_mount=BuilderState.fetch_components,  # <-- IMPORTANTE: on_mount aquí
    )