import uuid

from django.db import models


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codename = models.CharField(max_length=100, unique=True, help_text="Format: domain:action, e.g. stores:read")
    description = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["codename"]

    def __str__(self):
        return self.codename


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="roles")
    permissions = models.ManyToManyField(Permission, related_name="roles", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"], name="unique_role_name_per_tenant"),
        ]

    def __str__(self):
        return f"{self.name} ({self.tenant})"


class RoleBinding(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey("tenants.User", on_delete=models.CASCADE, related_name="role_bindings")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="bindings")
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE, related_name="role_bindings")
    company = models.ForeignKey(
        "tenants.Company", on_delete=models.CASCADE, related_name="role_bindings", null=True, blank=True
    )
    store = models.ForeignKey(
        "tenants.Store", on_delete=models.CASCADE, related_name="role_bindings", null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        scope = self.tenant.name
        if self.company:
            scope = self.company.name
        if self.store:
            scope = self.store.name
        return f"{self.user.email} -> {self.role.name} @ {scope}"
