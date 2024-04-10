from django.db import migrations, models


def lowercase_usernames(apps, schema_editor):
    User = apps.get_model('users', 'User')
    for user in User.objects.all():
        user.username = user.username.lower()
        user.save()


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_alter_user_email"),
    ]

    operations = [
        migrations.RunPython(lowercase_usernames),
    ]
