"""
FitBuddy ETL Data Migration Script: SQLite to PostgreSQL
Transfers User and WorkoutPlan records preserving primary keys, timestamps, and cascade integrity.
"""

import os
import sys
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, User, WorkoutPlan

SQLITE_PATH = os.getenv("SQLITE_PATH", "sqlite:///./app/data/fitbuddy.db")
POSTGRES_URL = os.getenv("TARGET_DATABASE_URL", "postgresql://fitbuddy_user:fitbuddy_secure_pass@localhost:5432/fitbuddy_db")

def run_migration():
    print("=== Starting SQLite to PostgreSQL ETL Migration ===")
    print(f"Source: {SQLITE_PATH}")
    print(f"Target: {POSTGRES_URL}")

    # 1. Source SQLite Engine
    sqlite_engine = create_engine(SQLITE_PATH, echo=False)
    SqliteSession = sessionmaker(bind=sqlite_engine)
    src_db = SqliteSession()

    # 2. Target PostgreSQL Engine
    pg_engine = create_engine(POSTGRES_URL, echo=False)
    PgSession = sessionmaker(bind=pg_engine)
    tgt_db = PgSession()

    try:
        # Create tables on target
        Base.metadata.create_all(bind=pg_engine)

        # Migrate Users
        users = src_db.execute(select(User)).scalars().all()
        print(f"Found {len(users)} User records in SQLite.")

        migrated_users = 0
        for u in users:
            existing_user = tgt_db.execute(select(User).where(User.user_id == u.user_id)).scalar_one_or_none()
            if not existing_user:
                new_u = User(
                    user_id=u.user_id,
                    name=u.name,
                    age=u.age,
                    weight=u.weight,
                    fitness_goal=u.fitness_goal,
                    intensity=u.intensity,
                    created_at=u.created_at,
                )
                tgt_db.add(new_u)
                migrated_users += 1

        tgt_db.commit()
        print(f"Migrated {migrated_users} Users to PostgreSQL.")

        # Migrate WorkoutPlans
        plans = src_db.execute(select(WorkoutPlan)).scalars().all()
        print(f"Found {len(plans)} WorkoutPlan records in SQLite.")

        migrated_plans = 0
        for p in plans:
            new_p = WorkoutPlan(
                user_id=p.user_id,
                original_plan=p.original_plan,
                nutrition_tip=p.nutrition_tip,
                updated_plan=p.updated_plan,
                feedback=p.feedback,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            tgt_db.add(new_p)
            migrated_plans += 1

        tgt_db.commit()
        print(f"Migrated {migrated_plans} WorkoutPlans to PostgreSQL.")
        print("=== Migration completed successfully! ===")

    except Exception as e:
        tgt_db.rollback()
        print(f" Migration failed: {str(e)}")
        sys.exit(1)
    finally:
        src_db.close()
        tgt_db.close()

if __name__ == "__main__":
    run_migration()
