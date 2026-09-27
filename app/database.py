"""
FitBuddy - Enterprise PostgreSQL & Async Persistence Layer
Supports PostgreSQL connection pooling with fallback compatibility for SQLite.
"""

import os
from datetime import datetime, timezone
from typing import Generator, List, Optional

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    sessionmaker,
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./fitbuddy.db",
)

# Configure production PostgreSQL connection pooling if postgresql, else SQLite
if "postgresql" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800,
        pool_pre_ping=True,
        echo=False,
        future=True,
    )
else:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,
        future=True,
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarative class for all SQLAlchemy models."""
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    fitness_goal: Mapped[str] = mapped_column(String(100), nullable=False)
    intensity: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    workout_plans: Mapped[List["WorkoutPlan"]] = relationship(
        "WorkoutPlan",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(WorkoutPlan.created_at)",
    )


class WorkoutPlan(Base):
    __tablename__ = "workout_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    original_plan: Mapped[str] = mapped_column(Text, nullable=False)
    nutrition_tip: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_plan: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="workout_plans")


def init_db() -> None:
    """Initialize relational database schema."""
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"Warning: Database initialization exception: {e}")


def get_db() -> Generator[Session, None, None]:
    """Yields thread-safe database session with automatic teardown."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_user(
    db: Session,
    user_id: str,
    name: str,
    age: int,
    weight: float,
    fitness_goal: str,
    intensity: str,
) -> User:
    """Atomically upsert user record."""
    stmt = select(User).where(User.user_id == user_id)
    user = db.execute(stmt).scalar_one_or_none()

    if user:
        user.name = name
        user.age = age
        user.weight = weight
        user.fitness_goal = fitness_goal
        user.intensity = intensity
    else:
        user = User(
            user_id=user_id,
            name=name,
            age=age,
            weight=weight,
            fitness_goal=fitness_goal,
            intensity=intensity,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return user


def save_plan(
    db: Session,
    user_id: str,
    original_plan: str,
    nutrition_tip: Optional[str] = None,
) -> WorkoutPlan:
    """Persist generated initial plan."""
    plan = WorkoutPlan(
        user_id=user_id,
        original_plan=original_plan,
        nutrition_tip=nutrition_tip,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(
    db: Session,
    user_id: str,
    updated_plan: str,
    feedback: str,
) -> Optional[WorkoutPlan]:
    """Update existing plan with feedback revision while preserving original_plan."""
    stmt = (
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user_id)
        .order_by(WorkoutPlan.created_at.desc())
    )
    plan = db.execute(stmt).scalars().first()

    if not plan:
        return None

    plan.updated_plan = updated_plan
    plan.feedback = feedback
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan


def get_original_plan(db: Session, user_id: str) -> Optional[WorkoutPlan]:
    """Retrieve latest plan for given user_id."""
    stmt = (
        select(WorkoutPlan)
        .where(WorkoutPlan.user_id == user_id)
        .order_by(WorkoutPlan.created_at.desc())
    )
    return db.execute(stmt).scalars().first()


def get_user(db: Session, user_id: str) -> Optional[User]:
    """Retrieve user by user_id."""
    stmt = select(User).where(User.user_id == user_id)
    return db.execute(stmt).scalar_one_or_none()


def get_all_users(db: Session) -> List[User]:
    """Retrieve all registered users with nested plans."""
    stmt = select(User).order_by(User.created_at.desc())
    return list(db.execute(stmt).scalars().all())
