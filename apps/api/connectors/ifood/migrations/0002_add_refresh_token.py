from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ifood", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="ifoodstorecredential",
            name="refresh_token",
            field=models.TextField(blank=True, default=""),
        ),
    ]
