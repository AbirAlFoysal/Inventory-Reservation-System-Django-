from django.db import models
from django.utils import timezone
import uuid

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self, deleted_by=None):
        return self.update(deleted_at=timezone.now(), deleted_by=deleted_by)

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def dead(self):
        return self.filter(deleted_at__isnull=False)

    def restore(self):
        return self.update(deleted_at=None, deleted_by=None)


class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_objects(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def dead(self):
        return SoftDeleteQuerySet(self.model, using=self._db).dead()


class BaseModel(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    objects = SoftDeleteManager()

    class Meta:
        abstract = True

    def delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_by = None
        self.deleted_at = None
        self.save()
