import databases
import sqlalchemy

DATABASE_URL = "postgresql://postgres_admin:TUM1idndU7mjoEhq7v@db"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "user",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String, index=True, unique=True, nullable=False),
    sqlalchemy.Column("email", sqlalchemy.String),
    sqlalchemy.Column("password_hash", sqlalchemy.String),
    sqlalchemy.Column("is_banned", sqlalchemy.Boolean)
)


engine = sqlalchemy.create_engine(
    DATABASE_URL
)
metadata.create_all(engine)

