# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PhotoDataset'
        db.create_table(u'photos_photodataset', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['photos.PhotoDataset'], null=True, blank=True)),
        ))
        db.send_create_signal(u'photos', ['PhotoDataset'])

        # Adding model 'FlickrUser'
        db.create_table(u'photos_flickruser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=127)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('sub_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('given_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('family_name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('website_name', self.gf('django.db.models.fields.CharField')(max_length=1023, blank=True)),
            ('website_url', self.gf('django.db.models.fields.URLField')(max_length=1023, blank=True)),
            ('blacklisted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'photos', ['FlickrUser'])

        # Adding model 'Photo'
        db.create_table(u'photos_photo', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['accounts.UserProfile'])),
            ('image_orig', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('name', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('orig_width', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('orig_height', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('aspect_ratio', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('exif', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('fov', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('focal_y', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('license', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='photos', null=True, to=orm['licenses.License'])),
            ('synthetic', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('inappropriate', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('nonperspective', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('stylized', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('rotated', self.gf('django.db.models.fields.NullBooleanField')(null=True, blank=True)),
            ('dataset', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='photos', null=True, to=orm['photos.PhotoDataset'])),
            ('flickr_user', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='photos', null=True, to=orm['photos.FlickrUser'])),
            ('flickr_id', self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True)),
            ('attribution_name', self.gf('django.db.models.fields.CharField')(max_length=127, blank=True)),
            ('attribution_url', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('md5', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal(u'photos', ['Photo'])


    def backwards(self, orm):
        # Deleting model 'PhotoDataset'
        db.delete_table(u'photos_photodataset')

        # Deleting model 'FlickrUser'
        db.delete_table(u'photos_flickruser')

        # Deleting model 'Photo'
        db.delete_table(u'photos_photo')


    models = {
        u'accounts.userprofile': {
            'Meta': {'object_name': 'UserProfile'},
            'always_approve': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'blocked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'blocked_reason': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'exclude_from_aggregation': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mturk_worker_id': ('django.db.models.fields.CharField', [], {'max_length': '127', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'user'", 'unique': 'True', 'primary_key': 'True', 'to': u"orm['auth.User']"})
        },
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'licenses.license': {
            'Meta': {'object_name': 'License'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'cc_attribution': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cc_no_deriv': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cc_noncommercial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'cc_share_alike': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'creative_commons': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'publishable': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'photos.flickruser': {
            'Meta': {'ordering': "['-id']", 'object_name': 'FlickrUser'},
            'blacklisted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'family_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'given_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sub_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'website_name': ('django.db.models.fields.CharField', [], {'max_length': '1023', 'blank': 'True'}),
            'website_url': ('django.db.models.fields.URLField', [], {'max_length': '1023', 'blank': 'True'})
        },
        u'photos.photo': {
            'Meta': {'ordering': "['aspect_ratio', '-id']", 'object_name': 'Photo'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'aspect_ratio': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'attribution_name': ('django.db.models.fields.CharField', [], {'max_length': '127', 'blank': 'True'}),
            'attribution_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'dataset': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'photos'", 'null': 'True', 'to': u"orm['photos.PhotoDataset']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'exif': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'flickr_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'flickr_user': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'photos'", 'null': 'True', 'to': u"orm['photos.FlickrUser']"}),
            'focal_y': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'fov': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image_orig': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'inappropriate': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'license': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'photos'", 'null': 'True', 'to': u"orm['licenses.License']"}),
            'md5': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'name': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'nonperspective': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'orig_height': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'orig_width': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'rotated': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'stylized': ('django.db.models.fields.NullBooleanField', [], {'null': 'True', 'blank': 'True'}),
            'synthetic': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['accounts.UserProfile']"})
        },
        u'photos.photodataset': {
            'Meta': {'ordering': "['name']", 'object_name': 'PhotoDataset'},
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '127'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['photos.PhotoDataset']", 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['photos']