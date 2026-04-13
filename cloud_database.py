"""
إدارة الاتصال بقاعدة البيانات السحابية
يدعم MySQL و PostgreSQL و MongoDB
"""

from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from config import settings


class CloudDatabaseManager:
    """مدير قاعدة البيانات السحابية"""
    
    def __init__(self):
        """تهيئة مدير قاعدة البيانات"""
        self.engine = None
        self.session_factory = None
        self.db_type = self._detect_db_type()
    
    def _detect_db_type(self) -> str:
        """الكشف عن نوع قاعدة البيانات من URL"""
        if not settings.database_url:
            return "sqlite"
        
        if "mysql" in settings.database_url:
            return "mysql"
        elif "postgresql" in settings.database_url:
            return "postgresql"
        elif "mongodb" in settings.database_url:
            return "mongodb"
        else:
            return "sqlite"
    
    def connect(self):
        """الاتصال بقاعدة البيانات"""
        try:
            if self.db_type == "mysql":
                self._connect_mysql()
            elif self.db_type == "postgresql":
                self._connect_postgresql()
            elif self.db_type == "mongodb":
                self._connect_mongodb()
            else:
                self._connect_sqlite()
            
            print(f"✅ تم الاتصال بقاعدة البيانات ({self.db_type}) بنجاح")
            return True
        
        except Exception as e:
            print(f"❌ خطأ في الاتصال بقاعدة البيانات: {str(e)}")
            return False
    
    def _connect_sqlite(self):
        """الاتصال بـ SQLite"""
        from sqlalchemy.pool import StaticPool
        
        self.engine = create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _connect_mysql(self):
        """الاتصال بـ MySQL"""
        self.engine = create_engine(
            settings.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _connect_postgresql(self):
        """الاتصال بـ PostgreSQL"""
        self.engine = create_engine(
            settings.database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
    
    def _connect_mongodb(self):
        """الاتصال بـ MongoDB"""
        from pymongo import MongoClient
        
        self.client = MongoClient(settings.database_url)
        self.db = self.client.get_database()
    
    def get_session(self):
        """الحصول على جلسة قاعدة البيانات"""
        if self.session_factory:
            return self.session_factory()
        return None
    
    def close(self):
        """إغلاق الاتصال"""
        if self.engine:
            self.engine.dispose()
        print("✅ تم إغلاق الاتصال بقاعدة البيانات")
    
    def health_check(self) -> bool:
        """فحص صحة الاتصال"""
        try:
            if self.db_type == "mongodb":
                self.db.command("ping")
            else:
                session = self.get_session()
                session.execute("SELECT 1")
                session.close()
            return True
        except Exception as e:
            print(f"❌ فشل فحص صحة الاتصال: {str(e)}")
            return False


# ==================== إعدادات الاتصال بقواعد البيانات السحابية ====================

"""
أمثلة على سلاسل الاتصال:

1. SQLite (محلي):
   DATABASE_URL=sqlite:///./yamenshat.db

2. MySQL:
   DATABASE_URL=mysql+pymysql://user:password@localhost:3306/yamenshat

3. PostgreSQL:
   DATABASE_URL=postgresql://user:password@localhost:5432/yamenshat

4. MongoDB:
   DATABASE_URL=mongodb+srv://user:password@cluster.mongodb.net/yamenshat

5. AWS RDS (MySQL):
   DATABASE_URL=mysql+pymysql://user:password@yamenshat.xxxxx.us-east-1.rds.amazonaws.com:3306/yamenshat

6. AWS RDS (PostgreSQL):
   DATABASE_URL=postgresql://user:password@yamenshat.xxxxx.us-east-1.rds.amazonaws.com:5432/yamenshat

7. Google Cloud SQL:
   DATABASE_URL=postgresql://user:password@/yamenshat?unix_socket=/cloudsql/project:region:instance

8. Azure Database:
   DATABASE_URL=postgresql://user@servername:password@servername.postgres.database.azure.com:5432/yamenshat
"""


class DatabaseConfig:
    """إعدادات قاعدة البيانات المختلفة"""
    
    @staticmethod
    def get_mysql_url(
        user: str,
        password: str,
        host: str,
        port: int = 3306,
        database: str = "yamenshat"
    ) -> str:
        """الحصول على URL الاتصال بـ MySQL"""
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"
    
    @staticmethod
    def get_postgresql_url(
        user: str,
        password: str,
        host: str,
        port: int = 5432,
        database: str = "yamenshat"
    ) -> str:
        """الحصول على URL الاتصال بـ PostgreSQL"""
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    @staticmethod
    def get_mongodb_url(
        user: str,
        password: str,
        cluster: str,
        database: str = "yamenshat"
    ) -> str:
        """الحصول على URL الاتصال بـ MongoDB"""
        return f"mongodb+srv://{user}:{password}@{cluster}.mongodb.net/{database}"
    
    @staticmethod
    def get_aws_rds_mysql_url(
        user: str,
        password: str,
        endpoint: str,
        database: str = "yamenshat"
    ) -> str:
        """الحصول على URL الاتصال بـ AWS RDS MySQL"""
        return f"mysql+pymysql://{user}:{password}@{endpoint}:3306/{database}"
    
    @staticmethod
    def get_aws_rds_postgresql_url(
        user: str,
        password: str,
        endpoint: str,
        database: str = "yamenshat"
    ) -> str:
        """الحصول على URL الاتصال بـ AWS RDS PostgreSQL"""
        return f"postgresql://{user}:{password}@{endpoint}:5432/{database}"
    
    @staticmethod
    def get_google_cloud_sql_url(
        user: str,
        password: str,
        instance_connection: str,
        database: str = "yamenshat"
    ) -> str:
        """الحصول على URL الاتصال بـ Google Cloud SQL"""
        return f"postgresql://{user}:{password}@/{database}?unix_socket=/cloudsql/{instance_connection}"
    
    @staticmethod
    def get_azure_database_url(
        user: str,
        password: str,
        server: str,
        database: str = "yamenshat"
    ) -> str:
        """الحصول على URL الاتصال بـ Azure Database"""
        return f"postgresql://{user}@{server}:{password}@{server}.postgres.database.azure.com:5432/{database}"


# إنشاء مثيل مدير قاعدة البيانات
cloud_db_manager = CloudDatabaseManager()
