from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, DateTime, func

if TYPE_CHECKING:
    from app.modules.usuario.models import Usuario


class DireccionEntrega(SQLModel, table=True):
    """Modelo de Dirección de Entrega - Asociado a un Usuario
    
    Un usuario puede tener múltiples direcciones de entrega.
    Solo UNA puede ser la principal (es_principal=True).
    """
    __tablename__ = "direccion_entrega"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    usuario_id: int = Field(
        foreign_key="usuario.id",
        nullable=False,
        index=True,
        description="Usuario propietario de esta dirección"
    )
    
    # Datos descriptivos
    alias: str = Field(
        max_length=50,
        nullable=False,
        description="Alias para identificar la dirección (ej: 'Casa', 'Trabajo', 'Gym')"
    )
    
    # Datos de la dirección
    calle: str = Field(
        max_length=200,
        nullable=False,
        description="Nombre de la calle"
    )
    
    numero: str = Field(
        max_length=20,
        nullable=False,
        description="Número de la calle"
    )
    
    apartamento: Optional[str] = Field(
        max_length=50,
        default=None,
        description="Número de apartamento, piso, etc."
    )
    
    localidad: str = Field(
        max_length=100,
        nullable=False,
        description="Localidad, barrio o zona"
    )
    
    codigo_postal: Optional[str] = Field(
        max_length=20,
        default=None,
        description="Código postal"
    )
    
    provincia: Optional[str] = Field(
        max_length=100,
        default=None,
        description="Provincia o estado"
    )
    
    notas: Optional[str] = Field(
        max_length=500,
        default=None,
        description="Notas adicionales (ej: 'Dejar en portería', 'Apartamento al fondo')"
    )
    
    # Direcciones principales
    es_principal: bool = Field(
        default=False,
        nullable=False,
        index=True,
        description="Es la dirección principal para entregas"
    )
    
    # Timestamps y auditoría
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column=Column(DateTime(timezone=True), onupdate=func.now(), nullable=False)
    )
    
    deleted_at: Optional[datetime] = Field(
        default=None,
        nullable=True,
        description="Soft delete timestamp"
    )
    
    # Relaciones
    usuario: "Usuario" = Relationship()

    def is_deleted(self) -> bool:
        """Verifica si la dirección está eliminada"""
        return self.deleted_at is not None

    def direccion_completa(self) -> str:
        """Retorna la dirección formateada completa"""
        partes = [self.calle, self.numero]
        
        if self.apartamento:
            partes.append(f"Apt/Piso {self.apartamento}")
        
        partes.append(self.localidad)
        
        if self.provincia:
            partes.append(self.provincia)
        
        if self.codigo_postal:
            partes.append(f"({self.codigo_postal})")
        
        return ", ".join(partes)
