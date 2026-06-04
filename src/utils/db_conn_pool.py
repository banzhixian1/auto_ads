import threading
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
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
        self._SessionFactory = sessionmaker(bind=self._engine)

    def get_session(self):
        """获取SQLAlchemy会话"""
        return self._SessionFactory()
    
    def query(self, sql: str, params: dict = None, fetchall: bool = None, return_dict: bool = None, session = None):
        """封装的快捷查询方法"""
        if fetchall is None:
            fetchall = True
        if return_dict is None:
            return_dict = True
        if session is None:
            inner_session = self.get_session()
        else:
            inner_session = session

        try:
            result = inner_session.execute(text(sql), params or {})
            if fetchall:
                rows = result.fetchall()

                if return_dict:
                    return [dict(r._mapping) for r in rows]
                return rows  # list(tuple)
            else:
                row = result.fetchone()
                if not row:
                    return None

                if return_dict:
                    return dict(row._mapping)
                return row  # tuple
        finally:
            if session is None:
                inner_session.close()

    def execute(self, sql: str, params: dict = None, session = None):
        """执行原始SQL语句"""
        if session is None:
            inner_session = self.get_session()
        else:
            inner_session = session
        try:
            result = inner_session.execute(text(sql), params or {})
            if session is None:
                inner_session.commit()
            return result.rowcount

        except Exception:
            if session is None:
                inner_session.rollback()
            raise
        finally:
            if session is None:
                inner_session.close()

from src.utils.configer import *
config_name = 'db_conn_pool'
mysql_default_value = {
    'host': '',
    'port': 3306,
    'user': '',
    'password': '',
}
pg_default_value = {
    'host': '',
    'port': 5432,
    'user': '',
    'password': '',
}
# 兼容旧配置节，同时为多连接场景初始化新的 default 节
init_config_section(config_name, 'mysql_default', mysql_default_value)
init_config_section(config_name, 'pg_default', pg_default_value)
config = read_config(config_name)

db_pool_lock = threading.Lock()
db_pool_instances: dict[str, SQLAlchemyPool] = {}

def _get_conn_section(db_type: str, conn_name: str) -> str:
    """
    获取连接配置节名称。格式 `<db_type>_<conn_name>`，
    """
    section = f'{db_type}_{conn_name}'
    if section in config:
        return section
    raise ValueError(f"配置文件 '{config_name}' 中不存在连接配置节: {section}")

def create_mysql_pool(
    database: str,
    conn_name: str = 'default',
    host: str = None,
    port: int = None,
    user: str = None,
    password: str = None,
    **kwargs,
) -> SQLAlchemyPool:
    section = _get_conn_section('mysql', conn_name)
    if host is None:
        host=config.get(section, 'host')
    if port is None:
        port=config.getint(section, 'port')
    if user is None:
        user=config.get(section, 'user')
    if password is None:
        password=config.get(section, 'password')

    db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    with db_pool_lock:
        if db_url not in db_pool_instances:
            mysql_pool = SQLAlchemyPool(db_url, **kwargs)
            db_pool_instances[db_url] = mysql_pool
    return db_pool_instances[db_url]

def create_pg_pool(
    database: str,
    conn_name: str = 'default',
    host: str = None,
    port: int = None,
    user: str = None,
    password: str = None,
    **kwargs,
) -> SQLAlchemyPool:
    section = _get_conn_section('pg', conn_name)
    if host is None:
        host=config.get(section, 'host')
    if port is None:
        port=config.getint(section, 'port')
    if user is None:
        user=config.get(section, 'user')
    if password is None:
        password=config.get(section, 'password')

    db_url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    with db_pool_lock:
        if db_url not in db_pool_instances:
            pg_pool = SQLAlchemyPool(db_url, **kwargs)
            db_pool_instances[db_url] = pg_pool
    return db_pool_instances[db_url]
