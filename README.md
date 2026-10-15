this is a new project for me to learn django



# backup db
Copy-Item .\db.sqlite3 ..\learnDjangoDBback\db_backup_20261012.sqlite3
python manage.py dumpdata --indent 2 --output ..\learnDjangoDBback\db_backup_20261012.json

# Django 的系统检查
python manage.py check

# 比较你现在的 models.py 和 Django 已记录的模型结构，生成一份数据库结构变更方案。
python manage.py makemigrations

# 执行迁移文件，真正调整数据库结构
python manage.py migrate

# 运行测试用例
python manage.py test hello
python manage.py test hello.tests.test_inbound_receive
python manage.py test hello.tests.test_inbound_item