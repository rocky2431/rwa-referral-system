"""
验证数据库表结构
检查所有表是否正确创建
"""

from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def verify_database_schema():
    """验证数据库架构"""
    print("🔍 开始验证数据库架构...\n")

    # 使用同步引擎
    database_url = os.getenv("DATABASE_URL", "postgresql://rocky243@localhost:5432/rwa_referral")
    print(f"📡 连接数据库: {database_url}\n")

    engine = create_engine(database_url, echo=False)

    with engine.connect() as conn:
        # 1. 检查表是否存在
        print("📋 检查表是否存在:")
        result = conn.execute(text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))

        tables = [row[0] for row in result]
        expected_tables = ['users', 'user_points', 'point_transactions', 'referral_relations', 'alembic_version']

        for table in expected_tables:
            if table in tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} (缺失)")

        print(f"\n   总计: {len(tables)} 个表")

        # 2. 检查 users 表结构
        print("\n📊 users 表字段:")
        result = conn.execute(text("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'users'
            ORDER BY ordinal_position
        """))

        for row in result:
            nullable = "NULL" if row[2] == 'YES' else "NOT NULL"
            default = f" DEFAULT {row[3]}" if row[3] else ""
            print(f"   - {row[0]:<25} {row[1]:<20} {nullable}{default}")

        # 3. 检查索引
        print("\n🔍 users 表索引:")
        result = conn.execute(text("""
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'users'
            AND indexname != 'users_pkey'
            ORDER BY indexname
        """))

        for row in result:
            print(f"   - {row[0]}")

        # 4. 检查外键约束
        print("\n🔗 外键约束:")
        result = conn.execute(text("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
            JOIN information_schema.referential_constraints AS rc
                ON rc.constraint_name = tc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            ORDER BY tc.table_name, kcu.column_name
        """))

        for row in result:
            print(f"   - {row[0]}.{row[1]} -> {row[2]}.{row[3]} (ON DELETE {row[4]})")

        # 5. 检查 CHECK 约束
        print("\n✓ CHECK 约束:")
        result = conn.execute(text("""
            SELECT
                tc.table_name,
                cc.constraint_name,
                cc.check_clause
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.check_constraints AS cc
                ON tc.constraint_name = cc.constraint_name
            WHERE tc.constraint_type = 'CHECK'
            ORDER BY tc.table_name, cc.constraint_name
        """))

        for row in result:
            print(f"   - {row[0]}.{row[1]}: {row[2]}")

        # 6. 检查枚举类型
        print("\n🏷️  枚举类型:")
        result = conn.execute(text("""
            SELECT
                t.typname as enum_name,
                e.enumlabel as enum_value
            FROM pg_type t
            JOIN pg_enum e ON t.oid = e.enumtypid
            JOIN pg_catalog.pg_namespace n ON n.oid = t.typnamespace
            WHERE n.nspname = 'public'
            ORDER BY t.typname, e.enumsortorder
        """))

        current_enum = None
        for row in result:
            if row[0] != current_enum:
                current_enum = row[0]
                print(f"\n   {current_enum}:")
            print(f"      - {row[1]}")

        print("\n✅ 数据库架构验证完成!\n")


if __name__ == "__main__":
    verify_database_schema()
