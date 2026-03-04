from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
import random, datetime

from erp_core.models import (
    Vendor, VendorContact, Item, ItemVendor, Department, CostCenter,
    PurchaseOrder, PurchaseOrderLine, GoodsReceipt, VendorInvoice,
    InventoryOnHand, InventoryTransaction, ExpenseAccount, Category,
    GLPosting, Budget, Approval, LegalEntity
)
from chatagent_app.models import ERPVectorDocument
from chatagent_app.utils.embeddings import generate_embedding

class Command(BaseCommand):
    help = "Create or update mock data for MVP testing (idempotent). Run multiple times to update masters."

    def handle(self, *args, **options):
        random.seed(42)
        today = datetime.date(2026,2,18)  # deterministic seed date for test reproducibility
        start_date = today - datetime.timedelta(days=730)

        self.stdout.write("Seeding master data...")
        # Legal Entities
        for i in range(1, 21):
            LegalEntity.objects.update_or_create(
                entity_id=f"ENT{i:02d}", 
                defaults={'entity_name': f"Entity {i:02d}"}
            )
        
        # Vendors
        vendor_groups = ['Local','Regional','International']
        for i in range(1,21):
            code = f"V{i:03d}"
            Vendor.objects.update_or_create(
                vendor_code=code,
                defaults={
                    'vendor_name': f"Vendor {i:02d}",
                    'vendor_group': vendor_groups[i % len(vendor_groups)],
                    'status': ['Approved','Pending','Blocked'][i % 3],
                    'last_transaction_date': None
                }
            )
        # Items
        item_groups = ['Raw Material','Finished Good','Service','MRO']
        for i in range(1,101):
            code = f"ITEM{i:04d}"
            Item.objects.update_or_create(
                item_code=code,
                defaults={
                    'item_name': f"Item {i:04d}",
                    'item_group': item_groups[i % len(item_groups)],
                    'unit_of_measure': ['EA','KG','M','L'][i % 4],
                    'reorder_level': float(10 + (i%20)*5)
                }
            )
        # Vendor Contacts
        for vendor in Vendor.objects.all():
            VendorContact.objects.update_or_create(
                vendor=vendor,
                contact_name=f"Contact for {vendor.vendor_name}",
                defaults={
                    'email': f"contact@{vendor.vendor_code.lower()}.com",
                    'phone': f"+1-{random.randint(100,999)}-{random.randint(1000,9999)}",
                    'is_primary': True
                }
            )
        # Departments and Cost Centers
        for i in range(1, 21):
            Department.objects.update_or_create(
                dept_id=f"D{i:02d}", 
                defaults={
                    'dept_name': f"Department {i:02d}", 
                    'entity_id': f"ENT{(i % 20) + 1:02d}"
                }
            )
        for i in range(1, 41):
            CostCenter.objects.update_or_create(
                cost_center_code=f"CC{i:03d}", 
                defaults={
                    'cost_center_name': f"CostCenter {i:03d}", 
                    'dept_id': f"D{(i % 20) + 1:02d}"
                }
            )

        # Category and Expense Account
        categories = [
            'Materials', 'Services', 'Freight', 'Travel', 'Marketing', 
            'IT Hardware', 'IT Software', 'Office Supplies', 'Maintenance', 'Utilities',
            'Legal', 'Consulting', 'Events', 'Training', 'Insurance',
            'Rent', 'Taxes', 'Audit', 'Security', 'Janitorial'
        ]
        cat_objs = []
        for i, cat_name in enumerate(categories, 1):
            cat_obj, _ = Category.objects.update_or_create(
                category_code=f"CAT{i:02d}",
                defaults={'category_name': cat_name}
            )
            cat_objs.append(cat_obj)

        account_objs = []
        for i in range(100, 120):
            acc_obj, _ = ExpenseAccount.objects.update_or_create(
                account_code=f"AC{i}",
                defaults={'account_name': f"Expense Account {i}"}
            )
            account_objs.append(acc_obj)

        # ItemVendor mapping (assign 1-3 vendors per item)
        vendors = list(Vendor.objects.values_list('vendor_code', flat=True))
        items = list(Item.objects.values_list('item_code', flat=True))
        for item_code in items:
            chosen = random.sample(vendors, random.randint(1,3))
            for v in chosen:
                ItemVendor.objects.update_or_create(item_id=item_code, vendor_id=v, defaults={
                    'is_approved': random.choice([True, True, False]),
                    'is_primary': False,
                    'last_purchase_price': round(random.uniform(5,500),2)
                })
        # Mark a primary vendor per item
        for item_code in items:
            ives = ItemVendor.objects.filter(item_id=item_code)
            if ives.exists():
                first = ives.first()
                ives.update(is_primary=False)
                first.is_primary = True
                first.save()

        self.stdout.write("Seeding procurement (POs, lines, receipts, invoices)...")
        # Create purchase orders and lines (idempotent by po_number)
        po_count = 500
        # Simpler deterministic approach: use incremental dates but spread over the range
        days_diff = (today - start_date).days
        vendors_list = list(Vendor.objects.values_list('vendor_code', flat=True))
        depts_list = list(Department.objects.values_list('dept_id', flat=True))
        cc_list = list(CostCenter.objects.values_list('cost_center_code', flat=True))
        line_counter = 1

        for i in range(1, po_count+1):
            po_number = f"PO{i:06d}"
            vendor = random.choice(vendors_list)
            dept = random.choice(depts_list)
            cost_center = random.choice(cc_list)
            # Distribute POs across the entire 2-year range
            # i/po_count * days_diff ensures we cover the whole span including today
            created_date = start_date + datetime.timedelta(days=int((i/po_count) * days_diff))
            status = random.choices(['Draft','Pending Approval','Approved','Received','Invoiced'], weights=[0.05,0.25,0.3,0.25,0.15])[0]
            approved_date = (created_date + datetime.timedelta(days=random.randint(1,10))) if status in ['Approved','Received','Invoiced'] else None
            total = 0.0
            n_lines = random.randint(1,5)
            po_obj, _ = PurchaseOrder.objects.update_or_create(
                po_number=po_number,
                defaults={
                    'vendor_id': vendor,
                    'dept_id': dept,
                    'cost_center_id': cost_center,
                    'created_date': created_date,
                    'approved_date': approved_date,
                    'status': status,
                    'total_value': 0.0
                }
            )
            # lines
            for ln in range(n_lines):
                item = random.choice(items)
                qty = round(random.uniform(1,200),2)
                unit_price = round(random.uniform(1,1000),2)
                line_total = round(qty * unit_price,2)
                expected_delivery = created_date + datetime.timedelta(days=random.randint(5,60))
                receipt_status = random.choice(['Pending','Partially Received','Received'])
                invoice_status = random.choice(['Pending','Matched','Invoiced'])
                PurchaseOrderLine.objects.update_or_create(
                    line_id=line_counter,
                    defaults={
                        'po_id': po_obj.po_number,
                        'item_id': item,
                        'warehouse': random.choice(['WH1','WH2','WH3']),
                        'quantity': qty,
                        'unit_price': unit_price,
                        'line_total': line_total,
                        'receipt_status': receipt_status,
                        'invoice_status': invoice_status,
                        'expected_delivery_date': expected_delivery
                    }
                )
                total += line_total
                line_counter += 1
            po_obj.total_value = round(total,2)
            po_obj.save()

        self.stdout.write("Seeding inventory transactions and balances...")
        # Create simple inventory transactions and balances derived from PO lines
        for pl in PurchaseOrderLine.objects.all()[:1200]:
            # create receipt for many lines
            qty_f = float(pl.quantity)
            received = round(min(qty_f, max(0, random.gauss(qty_f*0.9, qty_f*0.2))),2)
            receipt_date = pl.expected_delivery_date if pl.expected_delivery_date else (pl.po.created_date + datetime.timedelta(days=random.randint(1,60)))
            GoodsReceipt.objects.update_or_create(
                receipt_id=pl.line_id,
                defaults={
                    'po_line_id': pl.line_id,
                    'received_quantity': received,
                    'receipt_date': receipt_date,
                    'delivery_delay_days': (receipt_date - pl.po.created_date).days if pl.po.created_date else 0
                }
            )
            # inventory transaction
            InventoryTransaction.objects.update_or_create(
                transaction_id=None,
                defaults={
                    'item_id': pl.item_id,
                    'warehouse': pl.warehouse,
                    'transaction_type': 'Receipt',
                    'quantity': received,
                    'transaction_date': receipt_date,
                    'reference_type': 'PO',
                    'reference_id': pl.po_id
                }
            )
        # create random issue transactions
        for i in range(4500):
            it = random.choice(items)
            qty = round(random.uniform(0.5, 50),2)
            wh = random.choice(['WH1','WH2','WH3'])
            d = start_date + datetime.timedelta(days=random.randint(0, (today-start_date).days))
            InventoryTransaction.objects.create(
                item_id=it,
                warehouse=wh,
                transaction_type='Issue',
                quantity=-qty,
                transaction_date=d,
                reference_type='Issue',
                reference_id=None
            )

        # Recompute inventory on hand
        InventoryOnHand.objects.all().delete()
        from django.db.models import Sum
        balances = InventoryTransaction.objects.values('item_id','warehouse').annotate(quantity_on_hand=Sum('quantity'))
        for b in balances:
            InventoryOnHand.objects.update_or_create(
                item_id=b['item_id'],
                warehouse=b['warehouse'],
                defaults={'quantity_on_hand': b['quantity_on_hand']}
            )

        self.stdout.write("Seeding GL postings, budgets, invoices, approvals...")
        # GL postings
        for i in range(1,2001):
            entry_date = start_date + datetime.timedelta(days=random.randint(0, (today-start_date).days))
            GLPosting.objects.create(
                entry_date=entry_date,
                vendor_id=random.choice(vendors_list + [None]),
                dept_id=random.choice(depts_list),
                cost_center_id=random.choice(cc_list),
                category=random.choice(cat_objs),
                account=random.choice(account_objs),
                amount=round(random.uniform(100,50000),2) * (1 if random.random() < 0.7 else -1)
            )

        # Budgets
        category_objs = list(Category.objects.all())
        for cc in cc_list:
            for y in [today.year-1, today.year]:
                for m in range(1,13):
                    date_mid = datetime.date(y,m,15)
                    if start_date <= date_mid <= today:
                        # Map budget to a category as well for some records
                        cat = random.choice(category_objs) if random.random() > 0.3 else None
                        Budget.objects.update_or_create(
                            cost_center_id=cc,
                            fiscal_year=y,
                            fiscal_month=m,
                            category=cat,
                            defaults={'budget_amount': round(random.uniform(5000,50000),2)}
                        )
        from decimal import Decimal
        # Vendor invoices
        for i, po in enumerate(PurchaseOrder.objects.all()[:350], start=1):
            invoice_number = f"INV{i:06d}"
            invoice_date = po.created_date + datetime.timedelta(days=random.randint(1,90))
            VendorInvoice.objects.update_or_create(
                invoice_id=i,
                defaults={
                    'invoice_number': invoice_number,
                    'vendor_id': po.vendor_id,
                    'po_id': po.po_number,
                    'invoice_date': invoice_date,
                    'invoice_amount': round(po.total_value * Decimal(random.uniform(0.9,1.05)),2),
                    'status': random.choice(['Posted','Pending','Paid']),
                    'due_date': invoice_date + datetime.timedelta(days=30)
                }
            )
        # Approvals for many POs and invoices
        for po in PurchaseOrder.objects.all()[:300]:
            status = random.choices(['Pending','Approved','Rejected'], weights=[0.2,0.7,0.1])[0]
            created = po.created_date
            action = (created + datetime.timedelta(days=random.randint(1,14))) if status in ['Approved','Rejected'] else None
            Approval.objects.update_or_create(
                approval_id=None,
                document_type='PO',
                document_id=po.po_number,
                defaults={
                    'role_name': random.choice(['Purchasing Manager','Dept Head','Finance']),
                    'user_id': f"user{random.randint(1,20)}",
                    'status': status,
                    'created_date': created,
                    'action_date': action,
                    'rejection_reason': ('Quota exceeded' if status=='Rejected' else None)
                }
            )

        # Update Vendor last_transaction_date based on POs
        from django.db.models import Max
        vendor_dates = PurchaseOrder.objects.values('vendor_id').annotate(latest_po=Max('created_date'))
        for entry in vendor_dates:
            Vendor.objects.filter(vendor_code=entry['vendor_id']).update(last_transaction_date=entry['latest_po'])

        # === VECTOR SEEDING (Semantic Search) ===
        self.stdout.write("Seeding ERPVectorDocuments for semantic search...")
        ERPVectorDocument.objects.all().delete()

        vector_docs = []
        
        # Vendors
        for v in Vendor.objects.all():
            content = f"Vendor {v.vendor_code} ({v.vendor_name}) is a {v.vendor_group} supplier with status: {v.status}."
            vector_docs.append(ERPVectorDocument(
                content=content,
                source_model="Vendor",
                source_id=v.vendor_code,
                embedding=generate_embedding(content)
            ))

        # Items
        for it in Item.objects.all():
            content = f"Item {it.item_code} ({it.item_name}) belongs to the {it.item_group} group. Its unit of measure is {it.unit_of_measure} and reorder level is {it.reorder_level}."
            vector_docs.append(ERPVectorDocument(
                content=content,
                source_model="Item",
                source_id=it.item_code,
                embedding=generate_embedding(content)
            ))

        if vector_docs:
            ERPVectorDocument.objects.bulk_create(vector_docs)
            self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(vector_docs)} vector documents."))

        self.stdout.write(self.style.SUCCESS("Mock data seeding completed. Note: run again to update masters; for large reseeding, consider truncating tables first."))