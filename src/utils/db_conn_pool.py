import threading
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

class SQLAlchemyPool:
    def __init__(self, db_url: str, pool_size=5, max_overflow=10, pool_timeout=30, pre_ping=True):
        """
        db_url: 数据库 URL
        pool_size: 池中保持的连接数量
        max_overflow: 超过 pool_size 最大溢出连接数
        pool_timeout: 获取连接超时时间
        pre_ping: 取连接时检查有效性
        """
        self._engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_pre_ping=pre_ping,
            echo=False,
        )
        self._SessionFactory = scoped_session(sessionmaker(bind=self._engine))

    def get_session(self):
        """获取SQLAlchemy会话"""
        return self._SessionFactory()

    def execute(self, sql: str, params=None, fetchone=False, fetchall=False, return_type="tuple"):
        """执行原始SQL语句，可选获取结果。只是提供了方法，建议在外部获取会话，手动处理
        :param return_type: "tuple"（默认）, "dict"
        """
        session = self.get_session()
        try:
            result = session.execute(text(sql), params or {})

            # 基础数据读取
            if fetchone:
                row = result.fetchone()
                if not row:
                    return None

                if return_type == "dict":
                    return dict(row._mapping)
                return row  # tuple

            if fetchall:
                rows = result.fetchall()

                if return_type == "dict":
                    return [dict(r._mapping) for r in rows]
                return rows  # list(tuple)

            # 非查询类语句
            session.commit()
            return result.rowcount

        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

from src.utils.configer import *
config_name = 'db_conn_pool'
default_value = {
    'host': '',
    'port': 3306,
    'user': '',
    'password': '',
}
init_config_section(config_name, 'mysql', default_value)
default_value['port'] = 5432
init_config_section(config_name, 'pg', default_value)
config = read_config(config_name)

db_pool_lock = threading.Lock()
db_pool_instances: dict[str, SQLAlchemyPool] = {}

def create_mysql_pool(database: str=None, host: str=None, port: int=None, user: str=None, password: str=None, **kwargs) -> SQLAlchemyPool:
    if host is None:
        host=config.get('mysql', 'host')
    if port is None:
        port=config.getint('mysql', 'port')
    if user is None:
        user=config.get('mysql', 'user')
    if password is None:
        password=config.get('mysql', 'password')
    if database is None:
        db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}?charset=utf8mb4"
    else:
        db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    with db_pool_lock:
        if db_url not in db_pool_instances:
            mysql_pool = SQLAlchemyPool(db_url, **kwargs)
            db_pool_instances[db_url] = mysql_pool
    return db_pool_instances[db_url]

def create_pg_pool(database: str=None, host: str=None, port: int=None, user: str=None, password: str=None, **kwargs) -> SQLAlchemyPool:
    if host is None:
        host=config.get('pg', 'host')
    if port is None:
        port=config.getint('pg', 'port')
    if user is None:
        user=config.get('pg', 'user')
    if password is None:
        password=config.get('pg', 'password')
    if database is None:
        db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}?charset=utf8mb4"
    else:
        db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    with db_pool_lock:
        if db_url not in db_pool_instances:
            pg_pool = SQLAlchemyPool(db_url, **kwargs)
            db_pool_instances[db_url] = pg_pool
    return db_pool_instances[db_url]
