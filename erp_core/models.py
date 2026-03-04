from django.db import models


# =========================
# CORE ORGANIZATION
# =========================

class LegalEntity(models.Model):
    entity_id = models.CharField(max_length=20, primary_key=True)
    entity_name = models.CharField(max_length=100)

    def __str__(self):
        return self.entity_name


class Department(models.Model):
    dept_id = models.CharField(max_length=20, primary_key=True)
    dept_name = models.CharField(max_length=100)
    entity = models.ForeignKey(
        LegalEntity,
        on_delete=models.CASCADE,
        related_name="departments"
    )

    def __str__(self):
        return self.dept_name


class CostCenter(models.Model):
    cost_center_code = models.CharField(max_length=20, primary_key=True)
    cost_center_name = models.CharField(max_length=100)
    dept = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="cost_centers"
    )

    def __str__(self):
        return self.cost_center_name


# =========================
# VENDOR
# =========================

class Vendor(models.Model):
    STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Pending', 'Pending'),
        ('Blocked', 'Blocked'),
    ]

    vendor_code = models.CharField(max_length=20, primary_key=True)
    vendor_name = models.CharField(max_length=150)
    vendor_group = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    last_transaction_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.vendor_name


class VendorContact(models.Model):
    contact_id = models.AutoField(primary_key=True)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="contacts"
    )
    contact_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.contact_name} ({self.vendor.vendor_name})"


# =========================
# ITEM
# =========================

class Item(models.Model):
    item_code = models.CharField(max_length=20, primary_key=True)
    item_name = models.CharField(max_length=150)
    item_group = models.CharField(max_length=100, blank=True, null=True)
    unit_of_measure = models.CharField(max_length=20, blank=True, null=True)
    reorder_level = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.item_name


class ItemVendor(models.Model):
    id = models.AutoField(primary_key=True)
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="vendors"
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="items"
    )
    is_approved = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    last_purchase_price = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    class Meta:
        unique_together = ("item", "vendor")


# =========================
# PROCUREMENT
# =========================

class PurchaseOrder(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Pending Approval', 'Pending Approval'),
        ('Approved', 'Approved'),
        ('Received', 'Received'),
        ('Invoiced', 'Invoiced'),
    ]

    po_number = models.CharField(max_length=20, primary_key=True)
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name="purchase_orders"
    )
    dept = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="purchase_orders"
    )
    cost_center = models.ForeignKey(
        CostCenter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="purchase_orders"
    )
    created_date = models.DateField()
    approved_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    total_value = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        blank=True,
        null=True
    )

    def __str__(self):
        return self.po_number


class PurchaseOrderLine(models.Model):
    line_id = models.AutoField(primary_key=True)
    po = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="lines"
    )
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    warehouse = models.CharField(max_length=50, blank=True, null=True)
    quantity = models.DecimalField(max_digits=18, decimal_places=2)
    unit_price = models.DecimalField(max_digits=18, decimal_places=2)
    line_total = models.DecimalField(max_digits=18, decimal_places=2)
    receipt_status = models.CharField(max_length=20, blank=True, null=True)
    invoice_status = models.CharField(max_length=20, blank=True, null=True)
    expected_delivery_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.po.po_number} - {self.item.item_name}"


class GoodsReceipt(models.Model):
    receipt_id = models.AutoField(primary_key=True)
    po_line = models.ForeignKey(PurchaseOrderLine, on_delete=models.CASCADE)
    received_quantity = models.DecimalField(max_digits=18, decimal_places=2)
    receipt_date = models.DateField()
    delivery_delay_days = models.IntegerField(blank=True, null=True)


class VendorInvoice(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    invoice_number = models.CharField(max_length=30)
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    po = models.ForeignKey(PurchaseOrder, on_delete=models.SET_NULL, null=True)
    invoice_date = models.DateField()
    invoice_amount = models.DecimalField(max_digits=18, decimal_places=2)
    status = models.CharField(max_length=20)  # Posted, Pending, Paid
    due_date = models.DateField(blank=True, null=True)


# =========================
# INVENTORY
# =========================

class InventoryOnHand(models.Model):
    inventory_id = models.AutoField(primary_key=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    warehouse = models.CharField(max_length=50)
    quantity_on_hand = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        unique_together = ("item", "warehouse")


class InventoryTransaction(models.Model):
    transaction_id = models.AutoField(primary_key=True)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    warehouse = models.CharField(max_length=50)
    transaction_type = models.CharField(
        max_length=20
    )  # Receipt / Issue / Adjustment
    quantity = models.DecimalField(max_digits=18, decimal_places=2)
    transaction_date = models.DateField()
    reference_type = models.CharField(max_length=20, blank=True, null=True)
    reference_id = models.CharField(max_length=50, blank=True, null=True)


# =========================
# FINANCE
# =========================

class ExpenseAccount(models.Model):
    account_code = models.CharField(max_length=20, primary_key=True)
    account_name = models.CharField(max_length=100)

    def __str__(self):
        return self.account_name


class Category(models.Model):
    category_code = models.CharField(max_length=20, primary_key=True)
    category_name = models.CharField(max_length=100)

    def __str__(self):
        return self.category_name


class GLPosting(models.Model):
    gl_id = models.AutoField(primary_key=True)
    entry_date = models.DateField()
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    dept = models.ForeignKey(Department, on_delete=models.CASCADE)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    account = models.ForeignKey(ExpenseAccount, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=18, decimal_places=2)


class Budget(models.Model):
    budget_id = models.AutoField(primary_key=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    fiscal_year = models.IntegerField()
    fiscal_month = models.IntegerField()
    budget_amount = models.DecimalField(max_digits=18, decimal_places=2)


# =========================
# APPROVALS
# =========================

class Approval(models.Model):
    approval_id = models.AutoField(primary_key=True)
    document_type = models.CharField(max_length=20)  # PO, Invoice, etc.
    document_id = models.CharField(max_length=50)
    role_name = models.CharField(max_length=50)
    user_id = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20)  # Pending, Approved, Rejected
    created_date = models.DateField()
    action_date = models.DateField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)