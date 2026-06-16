"""Seed data para inicializar la base de datos con datos obligatorios

Este módulo se ejecuta al iniciar la aplicación (en el lifespan de FastAPI).
Popula la base de datos con:
- Roles (ADMIN, STOCK, PEDIDOS, CLIENT)
- Estados de Pedido (PENDIENTE, CONFIRMADO, EN_PREPARACION, EN_CAMINO, ENTREGADO, CANCELADO)
- Formas de Pago (TARJETA_CREDITO, TARJETA_DEBITO, EFECTIVO, TRANSFERENCIA, MERCADO_PAGO)
- Usuario Admin por defecto
"""

from sqlmodel import Session, select
from app.core.security import hash_password
from app.modules.usuario.models import Usuario, Rol, UsuarioRol
from app.modules.pedido.models import EstadoPedido, FormaPago
from app.modules.unidad_medida.model import UnidadMedida


def seed_roles(session: Session) -> None:
    """Popula los roles en la base de datos"""
    roles_data = [
        {"nombre": "ADMIN", "codigo": "ADMIN", "descripcion": "Administrador del sistema"},
        {"nombre": "STOCK", "codigo": "STOCK", "descripcion": "Gestor de stock y productos"},
        {"nombre": "PEDIDOS", "codigo": "PEDIDOS", "descripcion": "Gestor de pedidos"},
        {"nombre": "CLIENT", "codigo": "CLIENT", "descripcion": "Cliente"},
    ]
    
    for rol_data in roles_data:
        # Verificar si el rol ya existe
        existing = session.exec(
            select(Rol).where(Rol.nombre == rol_data["nombre"])
        ).first()
        
        if not existing:
            rol = Rol(
                nombre=rol_data["nombre"],
                codigo=rol_data["codigo"],
                descripcion=rol_data["descripcion"]
            )
            session.add(rol)
            print(f"✓ Rol creado: {rol_data['nombre']}")
        else:
            print(f"→ Rol ya existe: {rol_data['nombre']}")


def seed_admin_user(session: Session) -> None:
    """Crea el usuario administrador por defecto"""
    # Verificar si el usuario admin ya existe
    existing = session.exec(
        select(Usuario).where(Usuario.email == "admin@example.com")
    ).first()
    
    if existing:
        print("→ Usuario admin ya existe")
        return
    
    # Obtener el rol ADMIN
    rol_admin = session.exec(
        select(Rol).where(Rol.nombre == "ADMIN")
    ).first()
    
    if not rol_admin:
        print("✗ Rol ADMIN no encontrado. Ejecuta seed_roles() primero.")
        return
    
    # Generar hash bcrypt para contraseña por defecto: "admin123"
    password_hash = hash_password("admin123")

    # Crear usuario admin
    usuario_admin = Usuario(
        nombre="Administrador",
        apellido="Sistema",
        email="admin@example.com",
        password_hash=password_hash,
        activo=True
    )
    
    session.add(usuario_admin)
    session.flush()  # Para obtener el ID
    
    # Asignar rol ADMIN
    usuario_rol = UsuarioRol(
        usuario_id=usuario_admin.id,
        rol_id=rol_admin.id
    )
    session.add(usuario_rol)
    
    print(f"✓ Usuario admin creado: {usuario_admin.email}")


def seed_pedido_enums(session: Session) -> None:
    """
    Los enums de EstadoPedido y FormaPago se definen en el modelo,
    pero documentamos aquí cuáles son los valores válidos.
    
    EstadoPedido valores:
    - PENDIENTE
    - CONFIRMADO
    - EN_PREPARACION
    - EN_CAMINO
    - ENTREGADO
    - CANCELADO
    
    FormaPago valores:
    - TARJETA_CREDITO
    - TARJETA_DEBITO
    - EFECTIVO
    - TRANSFERENCIA
    - MERCADO_PAGO
    """
    print("✓ Estados de Pedido registrados: PENDIENTE, CONFIRMADO, EN_PREPARACION, EN_CAMINO, ENTREGADO, CANCELADO")
    print("✓ Formas de Pago registradas: TARJETA_CREDITO, TARJETA_DEBITO, EFECTIVO, TRANSFERENCIA, MERCADO_PAGO")


def seed_unidades_medida(session: Session) -> None:
    """Popula las unidades de medida de referencia (spec CE-05)"""
    unidades_data = [
        {"nombre": "kilogramo", "simbolo": "kg", "tipo": "peso"},
        {"nombre": "gramo", "simbolo": "g", "tipo": "peso"},
        {"nombre": "litro", "simbolo": "L", "tipo": "volumen"},
        {"nombre": "mililitro", "simbolo": "ml", "tipo": "volumen"},
        {"nombre": "unidad", "simbolo": "ud", "tipo": "contable"},
        {"nombre": "porción", "simbolo": "porciones", "tipo": "contable"},
    ]

    for u in unidades_data:
        existing = session.exec(
            select(UnidadMedida).where(UnidadMedida.simbolo == u["simbolo"])
        ).first()
        if not existing:
            session.add(UnidadMedida(**u))
            print(f"✓ UnidadMedida creada: {u['simbolo']}")
        else:
            print(f"→ UnidadMedida ya existe: {u['simbolo']}")


def seed_database(session: Session) -> None:
    """Ejecuta todos los seeds en orden correcto

    ORDEN IMPORTANTE:
    1. Roles (dependencia de Usuario)
    2. Usuario Admin
    3. Enums (solo documentación)
    4. Unidades de Medida
    """
    print("\n" + "="*50)
    print("🌱 INICIANDO SEED DATA")
    print("="*50 + "\n")
    
    try:
        seed_roles(session)
        session.flush()
        print()
        
        seed_admin_user(session)
        session.flush()
        print()
        
        seed_pedido_enums(session)
        print()

        seed_unidades_medida(session)
        session.flush()
        print()

        print("="*50)
        print("✅ SEED DATA COMPLETADO")
        print("="*50 + "\n")
        
    except Exception as e:
        session.rollback()
        print(f"\n✗ ERROR en seed data: {str(e)}")
        raise
