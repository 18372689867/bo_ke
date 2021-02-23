from celery import Celery
from django.conf import settings
import os

# 1 添加环境变量，告诉celery为哪一个Django项目提供服务
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'ddblog.settings')
# 2 创建Celery对象
app = Celery('ddblog')

# 3 配置Celery
app.conf.update(
    BROKER_URL ='redis://@127.0.0.1:6379/1'
)
# 4 告知celery 自动到Django项目的应用下查找任务函数
app.autodiscover_tasks(settings.INSTALLED_APPS)