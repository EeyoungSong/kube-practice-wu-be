#!/usr/bin/env python
"""
RDS 연결 테스트 스크립트
EC2에서 실행하여 RDS 연결을 확인합니다.
"""
import os
import sys
import django
from django.conf import settings
from django.db import connection
from django.core.management import execute_from_command_line

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_database_connection():
    """데이터베이스 연결 테스트"""
    try:
        # 데이터베이스 연결 테스트
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        print("✅ 데이터베이스 연결 성공!")
        print(f"📍 DB Host: {settings.DATABASES['default']['HOST']}")
        print(f"📍 DB Name: {settings.DATABASES['default']['NAME']}")
        print(f"📍 DB User: {settings.DATABASES['default']['USER']}")
        print(f"📍 DB Port: {settings.DATABASES['default']['PORT']}")
        
        # 테이블 목록 확인
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        print(f"📊 테이블 수: {len(tables)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False

def test_migrations():
    """마이그레이션 상태 확인"""
    try:
        from django.db.migrations.executor import MigrationExecutor
        
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print(f"⚠️  적용되지 않은 마이그레이션 {len(plan)}개 발견")
            for migration, backwards in plan:
                print(f"   - {migration}")
        else:
            print("✅ 모든 마이그레이션이 적용되었습니다!")
            
        return len(plan) == 0
        
    except Exception as e:
        print(f"❌ 마이그레이션 확인 실패: {e}")
        return False

if __name__ == "__main__":
    print("🔍 RDS 연결 테스트 시작...")
    print("=" * 50)
    
    # 데이터베이스 연결 테스트
    db_ok = test_database_connection()
    print()
    
    # 마이그레이션 상태 확인
    if db_ok:
        migration_ok = test_migrations()
        print()
        
        if migration_ok:
            print("🎉 모든 테스트 통과!")
        else:
            print("⚠️  마이그레이션을 실행해주세요: python manage.py migrate")
    else:
        print("❌ 데이터베이스 연결을 먼저 확인해주세요.")
        
    print("=" * 50)

