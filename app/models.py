from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(50), default="admin")  # admin / storekeeper / technician
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Warehouse(Base):
    __tablename__ = "warehouses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shelves: Mapped[list["Shelf"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")

class Shelf(Base):
    __tablename__ = "shelves"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"))
    code: Mapped[str] = mapped_column(String(80), index=True)  # مثال: WH1-R01-S01
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    warehouse: Mapped["Warehouse"] = relationship(back_populates="shelves")
    equipment: Mapped[list["Equipment"]] = relationship(back_populates="shelf")

class Equipment(Base):
    __tablename__ = "equipment"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(30), unique=True, index=True)  # EQ-000001
    name: Mapped[str] = mapped_column(String(255), index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    serial_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    asset_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="جاهزة")  # جاهزة/قيد التشغيل/تحت الصيانة/تالفة/مؤجرة
    shelf_id: Mapped[int | None] = mapped_column(ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    shelf: Mapped["Shelf"] = relationship(back_populates="equipment")
    movements: Mapped[list["Movement"]] = relationship(back_populates="equipment", cascade="all, delete-orphan")

class Movement(Base):
    __tablename__ = "movements"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    equipment_id: Mapped[int] = mapped_column(ForeignKey("equipment.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(30))  # صرف/تسليم/استلام/نقل/تأجير/إرجاع
    to_person: Mapped[str | None] = mapped_column(String(255), nullable=True)
    project: Mapped[str | None] = mapped_column(String(255), nullable=True)
    from_shelf: Mapped[str | None] = mapped_column(String(80), nullable=True)
    to_shelf: Mapped[str | None] = mapped_column(String(80), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    equipment: Mapped["Equipment"] = relationship(back_populates="movements")
