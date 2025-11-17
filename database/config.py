# database/config.py
import mysql.connector
from mysql.connector import Error
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# 统一的数据库配置
DB_CONFIG = {
    'host': 'mysql2.sqlpub.com',
    'port': 3307,
    'database': 'dxshenwebappdb',
    'user': 'dxshen',
    'password': 'iXR2bGPwZ9rmzrhm',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
    'use_unicode': True,
    'autocommit': False,
    'connect_timeout': 10,
    'ssl_disabled': False,
    'ssl_verify_identity': False
}

def get_db_connection():
    """获取数据库连接"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        logger.debug("数据库连接成功")
        return connection
    except Error as e:
        logger.error(f"数据库连接失败: {e}")
        return None

@contextmanager
def get_db_connection_context():
    """使用上下文管理器自动处理连接的打开和关闭"""
    connection = None
    try:
        connection = get_db_connection()
        if connection is None:
            raise Exception("无法建立数据库连接")
        yield connection
    except Exception as e:
        logger.error(f"数据库连接上下文错误: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()
            logger.debug("数据库连接已关闭")

# 改进的简化封装
def query_one(sql, params=None):
    """查询单条记录"""
    with get_db_connection_context() as conn:
        with conn.cursor(dictionary=True) as cursor:  # ✅ 使用游标的上下文管理器
            cursor.execute(sql, params or ())
            return cursor.fetchone()

def query_all(sql, params=None):
    """查询所有记录"""
    with get_db_connection_context() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()

def execute(sql, params=None):
    """执行更新操作"""
    with get_db_connection_context() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            affected = cursor.rowcount
            conn.commit()
            return affected

def execute_many(operations):
    """执行多个操作（事务）"""
    with get_db_connection_context() as conn:
        with conn.cursor() as cursor:
            for sql, params in operations:
                cursor.execute(sql, params or ())
            conn.commit()
            return True

def test_connection():
    """测试数据库连接"""
    try:
        result = query_one("SELECT 1 as test")
        return True, "数据库连接正常" if result else "测试查询返回空结果"
    except Exception as e:
        return False, f"数据库测试失败: {e}"