from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from config import Config
import logging

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(Config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully")

def create_default_templates(db: Session):
    """Create default templates if they don't exist"""
    from database.models import Template
    
    # Check if default templates already exist
    existing_templates = db.query(Template).filter(Template.is_default == True).count()
    if existing_templates > 0:
        return
    
    # Create default templates
    default_templates = [
        Template(name="Формальный", prompt="Перепиши этот текст в формальном стиле, сохранив основную мысль:", is_default=True),
        Template(name="Разговорный", prompt="Перепиши этот текст в разговорном стиле, сделав его более дружелюбным:", is_default=True),
        Template(name="Профессиональный", prompt="Перепиши этот текст в профессиональном стиле для деловой аудитории:", is_default=True),
        Template(name="Креативный", prompt="Перепиши этот текст в креативном стиле, добавив яркие образы:", is_default=True),
        Template(name="Краткий", prompt="Сократи этот текст, оставив только самое важное:", is_default=True),
        Template(name="Расширенный", prompt="Расширь этот текст, добавив больше деталей и объяснений:", is_default=True),
    ]
    
    for template in default_templates:
        db.add(template)
    
    db.commit()
    logger.info("Default templates created successfully") 