"""测试配置加载"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings, _yaml_config, _load_config_yaml

print("=" * 60)
print("配置加载诊断")
print("=" * 60)

# 1. 检查当前工作目录
print(f"\n1. 当前工作目录: {Path.cwd()}")

# 2. 检查 config.yaml 是否存在
config_path = Path("../config.yaml")
print(f"\n2. config.yaml 是否存在: {config_path.exists()}")
print(f"   完整路径: {config_path.absolute()}")

# 3. 检查原始 YAML 内容
print(f"\n3. 原始 YAML 内容:")
if _yaml_config:
    for key, value in _yaml_config.items():
        print(f"   {key}: {value}")
else:
    print("   ❌ YAML 配置为空！")

# 4. 检查展平后的配置
print(f"\n4. 展平后的配置字段（部分）:")
important_fields = [
    'siliconflow_api_key',
    'siliconflow_base_url',
    'embedding_model',
    'llm_model',
    'app_port',
    'redis_enabled'
]

for field in important_fields:
    value = getattr(settings, field, "NOT_FOUND")
    print(f"   {field}: {value}")

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
