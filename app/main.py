import os
import urllib.parse
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import Field, Session, SQLModel, create_engine, select, func, col

# SQL tables

class Workflow(SQLModel, table=True):
    # Keep class name Pythonic while still mapping to actual SQL table
    __tablename__: str = "workflow_entity" # type: ignore

    id: str = Field(primary_key=True, unique=True, nullable=False)

class Execution(SQLModel, table=True):
    # Keep class name Pythonic while still mapping to actual SQL table
    __tablename__: str = "execution_entity" # type: ignore

    id: int = Field(primary_key=True, nullable=False)

# SQL server details

postgresql_username = os.getenv("POSTGRES_USER", default="postgres")
postgresql_password = urllib.parse.quote(os.getenv("POSTGRES_PASSWORD", default=""), safe="") # Special characters can break URI
postgresql_host = os.getenv("POSTGRES_HOST", default="localhost")
postgresql_port = os.getenv("POSTGRES_PORT", default="5432")
postgresql_db = os.getenv("POSTGRES_DB", default="n8n")

postgresql_url = f"postgresql://{postgresql_username}:{postgresql_password}@{postgresql_host}:{postgresql_port}/{postgresql_db}"

connect_args = {}
engine = create_engine(postgresql_url, connect_args=connect_args)

# Example code for sqlite:
# sqlite_file_name = "test.db"
# sqlite_url = f"sqlite:///{sqlite_file_name}"
# connect_args = {"check_same_thread": False}
# engine = create_engine(sqlite_url, connect_args=connect_args)

# SQL server connection functions

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# FastAPI functionality

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root(session: SessionDep):
    # Equivalent of SELECT COUNT(*) FROM workflow_entity;
    statement = select(func.count(col(Workflow.id)))
    workflows = session.exec(statement).one()
    if not workflows:
        raise HTTPException(status_code=404, detail="Workflow count not found")
    
    # Equivalent of SELECT COUNT(*) FROM execution_entity;
    statement = select(func.count(col(Execution.id)))
    executions = session.exec(statement).one()
    if not executions:
        raise HTTPException(status_code=404, detail="Execution count not found")

    return {
        "workflows": workflows,
        "executions": executions
    }
