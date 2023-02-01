# Generated by Django 3.2.9 on 2023-02-01 05:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('documents', '0001_initial'),
        ('analyzer', '0002_initial'),
        ('annotations', '0001_initial'),
        ('corpuses', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='relationshipuserobjectpermission',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='relationshipgroupobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.relationship'),
        ),
        migrations.AddField(
            model_name='relationshipgroupobjectpermission',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
        migrations.AddField(
            model_name='relationshipgroupobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='analyzer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='analyzer.analyzer'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='corpus',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='corpuses.corpus'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='creator',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='relationship',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='documents.document'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='relationship_label',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='annotations.annotationlabel'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='source_annotations',
            field=models.ManyToManyField(blank=True, related_name='source_node_in_relationships', related_query_name='source_node_in_relationship', to='annotations.Annotation'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='target_annotations',
            field=models.ManyToManyField(blank=True, related_name='target_node_in_relationships', related_query_name='target_node_in_relationship', to='annotations.Annotation'),
        ),
        migrations.AddField(
            model_name='relationship',
            name='user_lock',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locked_relationship_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='labelsetuserobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.labelset'),
        ),
        migrations.AddField(
            model_name='labelsetuserobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission'),
        ),
        migrations.AddField(
            model_name='labelsetuserobjectpermission',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='labelsetgroupobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.labelset'),
        ),
        migrations.AddField(
            model_name='labelsetgroupobjectpermission',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
        migrations.AddField(
            model_name='labelsetgroupobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission'),
        ),
        migrations.AddField(
            model_name='labelset',
            name='analyzer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='analyzer.analyzer'),
        ),
        migrations.AddField(
            model_name='labelset',
            name='annotation_labels',
            field=models.ManyToManyField(blank=True, related_name='included_in_labelsets', related_query_name='included_in_labelset', to='annotations.AnnotationLabel'),
        ),
        migrations.AddField(
            model_name='labelset',
            name='creator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='labelset',
            name='user_lock',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locked_labelset_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='annotationuserobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.annotation'),
        ),
        migrations.AddField(
            model_name='annotationuserobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission'),
        ),
        migrations.AddField(
            model_name='annotationuserobjectpermission',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='annotationlabeluserobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.annotationlabel'),
        ),
        migrations.AddField(
            model_name='annotationlabeluserobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission'),
        ),
        migrations.AddField(
            model_name='annotationlabeluserobjectpermission',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='annotationlabelgroupobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.annotationlabel'),
        ),
        migrations.AddField(
            model_name='annotationlabelgroupobjectpermission',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
        migrations.AddField(
            model_name='annotationlabelgroupobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission'),
        ),
        migrations.AddField(
            model_name='annotationlabel',
            name='analyzer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='analyzer.analyzer'),
        ),
        migrations.AddField(
            model_name='annotationlabel',
            name='creator',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='annotationlabel',
            name='user_lock',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locked_annotationlabel_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='annotationgroupobjectpermission',
            name='content_object',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='annotations.annotation'),
        ),
        migrations.AddField(
            model_name='annotationgroupobjectpermission',
            name='group',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.group'),
        ),
        migrations.AddField(
            model_name='annotationgroupobjectpermission',
            name='permission',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.permission'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='analysis',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotations', to='analyzer.analysis'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='annotation_label',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='annotations.annotationlabel'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='corpus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='annotations', to='corpuses.corpus'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='creator',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='annotation',
            name='document',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='doc_annotations', related_query_name='doc_annotation', to='documents.document'),
        ),
        migrations.AddField(
            model_name='annotation',
            name='user_lock',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='locked_annotation_objects', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='relationshipuserobjectpermission',
            unique_together={('user', 'permission', 'content_object')},
        ),
        migrations.AlterUniqueTogether(
            name='relationshipgroupobjectpermission',
            unique_together={('group', 'permission', 'content_object')},
        ),
        migrations.AlterUniqueTogether(
            name='labelsetuserobjectpermission',
            unique_together={('user', 'permission', 'content_object')},
        ),
        migrations.AlterUniqueTogether(
            name='labelsetgroupobjectpermission',
            unique_together={('group', 'permission', 'content_object')},
        ),
        migrations.AddConstraint(
            model_name='labelset',
            constraint=models.UniqueConstraint(fields=('analyzer', 'title'), name='Only install one labelset of given title for each analyzer (no duplicates)'),
        ),
        migrations.AlterUniqueTogether(
            name='annotationuserobjectpermission',
            unique_together={('user', 'permission', 'content_object')},
        ),
        migrations.AlterUniqueTogether(
            name='annotationlabeluserobjectpermission',
            unique_together={('user', 'permission', 'content_object')},
        ),
        migrations.AlterUniqueTogether(
            name='annotationlabelgroupobjectpermission',
            unique_together={('group', 'permission', 'content_object')},
        ),
        migrations.AddConstraint(
            model_name='annotationlabel',
            constraint=models.UniqueConstraint(fields=('analyzer', 'text'), name='Only install one label of given name for each analyzer_id (no duplicates)'),
        ),
        migrations.AlterUniqueTogether(
            name='annotationgroupobjectpermission',
            unique_together={('group', 'permission', 'content_object')},
        ),
    ]
