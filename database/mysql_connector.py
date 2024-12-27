from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
import threading
import logging
import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 导入配置
from database.config import DB_CONFIG

logger = logging.getLogger(__name__)

# 创建数据库URL
DATABASE_URL = (
    f"mysql+mysqldb://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    "?charset=utf8mb4"
)

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()
    _local = threading.local()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseManager, cls).__new__(cls)
                cls._instance._init_engine()
            return cls._instance

    def _init_engine(self):
        self.engine = create_engine(
            DATABASE_URL,
            echo=False,
            poolclass=QueuePool,
            pool_size=20,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800
        )
        self.session_factory = sessionmaker(bind=self.engine)
        self.Session = scoped_session(self.session_factory)

    def get_session(self):
        if not hasattr(self._local, 'session'):
            self._local.session = self.Session()
        return self._local.session

    def close_session(self):
        if hasattr(self._local, 'session'):
            self._local.session.close()
            self.Session.remove()
            delattr(self._local, 'session')

db_manager = DatabaseManager()

# 使用绝对导入
from database.base import Base, engine
from utils.logger import logger

def init_db():
    """初始化数据库（创建所有表）"""
    try:
        # 测试数据库连接
        with engine.connect() as conn:
            logger.info("数据库连接成功")
            result = conn.execute(text("SELECT DATABASE()"))
            current_db = result.scalar()
            logger.info(f"当前数据库: {current_db}")
        
        print("正在导入实体类...")
        # 导入并打印每个实体类的信息
        from entities.dialogue import Dialogue
        print(f"Dialogue 表名: {Dialogue.__tablename__}")
        
        from entities.narrative import Narrative
        print(f"Narrative 表名: {Narrative.__tablename__}")
        
        from entities.paragraph import Paragraph
        print(f"Paragraph 表名: {Paragraph.__tablename__}")
        
        from entities.tag import Tag
        print(f"Tag 表名: {Tag.__tablename__}")
        
        # 打印所有已注册的表
        print("\n开始创建数据库表...")
        tables = Base.metadata.tables
        print(f"已注册的表: {tables.keys()}")
        for table_name, table in tables.items():
            print(f"表 {table_name} 的列: {[c.name for c in table.columns]}")
        
        # 创建表
        Base.metadata.create_all(bind=engine)
        
        # 验证表是否创建成功
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        print(f"\n数据库中的表: {created_tables}")
        
        if not created_tables:
            print("\n警告: 没有表被创建！")
            print("Base.metadata.tables 内容:", Base.metadata.tables)
        else:
            print("\n数据库表创建成功")
            # 打印每个表的结构
            for table_name in created_tables:
                columns = inspector.get_columns(table_name)
                print(f"\n表 {table_name} 的结构:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
        
    except Exception as e:
        logger.error(f"初始化数据库时发生错误: {str(e)}")
        import traceback
        print(traceback.format_exc())
        raise

if __name__ == "__main__":
    init_db() 