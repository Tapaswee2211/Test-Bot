# models.py in root
from sqlalchemy import Column, String, Integer, Text
from .db import Base, engine

class OAuthToken(Base):
    __tablename__ = "oauth_tokens"
    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String, index=True)
    access_token = Column(String)
    refresh_token = Column(String)
    expires_at = Column(Integer)
    auth_user = Column(String)
    auth_ps_list = Column(Text, nullable=True)

# Call this ONLY after the class is defined
def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
