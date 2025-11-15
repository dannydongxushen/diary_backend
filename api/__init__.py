from .auth import auth_bp

# 这样可以直接从 api 导入 auth_bp
__all__ = ['auth_bp']