from .auth import auth_bp
from .diaries import diaries_bp  # 新增导入

# 这样可以直接从 api 导入 auth_bp 和 diaries_bp
__all__ = ['auth_bp', 'diaries_bp']