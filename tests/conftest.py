import pytest
from sqlalchemy import create_engine, text, event
from sqlalchemy.orm import sessionmaker
from database.base import Base
from database.config import DB_CONFIG

# 使用测试数据库
TEST_DATABASE_URL = (
    f"mysql+mysqldb://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/memory_tree_test"
    "?charset=utf8mb4&collation=utf8mb4_unicode_ci"
)

@pytest.fixture(scope="session")
def engine():
    """创建测试数据库引擎"""
    # 先创建测试数据库
    temp_engine = create_engine(
        f"mysql+mysqldb://{DB_CONFIG['user']}:{DB_CONFIG['password']}@"
        f"{DB_CONFIG['host']}:{DB_CONFIG['port']}"
    )
    with temp_engine.connect() as conn:
        conn.execute(text("DROP DATABASE IF EXISTS memory_tree_test"))
        conn.execute(text(
            "CREATE DATABASE memory_tree_test "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        ))
    temp_engine.dispose()

    # 创建测试数据库连接
    test_engine = create_engine(
        TEST_DATABASE_URL,
        echo=True,
        pool_pre_ping=True,
        connect_args={
            'charset': 'utf8mb4',
            'init_command': 
                'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;'
                'SET CHARACTER SET utf8mb4;'
                'SET SESSION collation_connection = utf8mb4_unicode_ci;'
        }
    )
    
    yield test_engine
    test_engine.dispose()

@pytest.fixture(scope="session")
def tables(engine):
    """创建测试数据库表"""
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(engine, tables):
    """创建数据库会话"""
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection)
    session = Session()

    yield session

    session.close()
    transaction.rollback()
    connection.close() 