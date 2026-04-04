-- Seed Data for ERP Analytics Chatbot

-- Legal Entities
INSERT INTO erp_core_legalentity (entity_id, entity_name) VALUES
('ENT01', 'TechCorp Global'),
('ENT02', 'Loomis Manufacturing');

-- Departments
INSERT INTO erp_core_department (dept_id, dept_name, entity_id) VALUES
('DEPT-IT', 'Information Technology', 'ENT01'),
('DEPT-HR', 'Human Resources', 'ENT01'),
('DEPT-PROD', 'Production', 'ENT02'),
('DEPT-SALES', 'Sales & Marketing', 'ENT02');

-- Cost Centers
INSERT INTO erp_core_costcenter (cost_center_code, cost_center_name, dept_id) VALUES
('CC-IT-01', 'Infrastructure', 'DEPT-IT'),
('CC-IT-02', 'Software Dev', 'DEPT-IT'),
('CC-PROD-01', 'Assembly Line A', 'DEPT-PROD'),
('CC-SALES-01', 'Direct Sales', 'DEPT-SALES');

-- Categories
INSERT INTO erp_core_category (category_code, category_name) VALUES
('CAT-HW', 'Hardware'),
('CAT-SW', 'Software'),
('CAT-RAW', 'Raw Materials'),
('CAT-MKT', 'Marketing Expenses');

-- Expense Accounts
INSERT INTO erp_core_expenseaccount (account_code, account_name) VALUES
('ACC-501', 'IT Equipment'),
('ACC-502', 'SaaS Licenses'),
('ACC-601', 'Raw Material Inventory'),
('ACC-701', 'Advertising');

-- Vendors
INSERT INTO erp_core_vendor (vendor_code, vendor_name, vendor_group, status, last_transaction_date) VALUES
('V001', 'Global Systems Inc', 'IT Services', 'Approved', '2025-01-15'),
('V002', 'Steel & Co', 'Manufacturing', 'Approved', '2025-02-10'),
('V003', 'AdAstro Media', 'Marketing', 'Pending', '2024-12-01'),
('V004', 'CloudServices Ltd', 'IT Services', 'Approved', '2025-03-01');

-- Items
INSERT INTO erp_core_item (item_code, item_name, item_group, unit_of_measure, reorder_level) VALUES
('ITEM001', 'Dell Precision 7000', 'Hardware', 'EA', 5.00),
('ITEM002', 'MacBook Pro 16', 'Hardware', 'EA', 10.00),
('ITEM003', 'Steel Sheet 5mm', 'Raw Material', 'KG', 1000.00),
('ITEM004', 'Office 365 License', 'Software', 'EA', 0.00);

-- Item Vendors
INSERT INTO erp_core_itemvendor (item_id, vendor_id, is_approved, is_primary, last_purchase_price) VALUES
('ITEM001', 'V001', true, true, 2500.00),
('ITEM002', 'V001', true, true, 3000.00),
('ITEM003', 'V002', true, true, 50.00);

-- Purchase Orders
INSERT INTO erp_core_purchaseorder (po_number, vendor_id, dept_id, cost_center_id, created_date, approved_date, status, total_value) VALUES
('PO-2025-001', 'V001', 'DEPT-IT', 'CC-IT-01', '2025-01-10', '2025-01-11', 'Approved', 12500.00),
('PO-2025-002', 'V002', 'DEPT-PROD', 'CC-PROD-01', '2025-02-05', '2025-02-06', 'Approved', 25000.00),
('PO-2025-003', 'V004', 'DEPT-IT', 'CC-IT-02', '2025-03-01', NULL, 'Pending Approval', 5400.00);

-- PO Lines
INSERT INTO erp_core_purchaseorderline (po_id, item_id, warehouse, quantity, unit_price, line_total, receipt_status, invoice_status, expected_delivery_date) VALUES
('PO-2025-001', 'ITEM001', 'WH-SAN-JOSE', 5.00, 2500.00, 12500.00, 'Received', 'Invoiced', '2025-01-15'),
('PO-2025-002', 'ITEM003', 'WH-DETROIT', 500.00, 50.00, 25000.00, 'Pending', 'Pending', '2025-02-20'),
('PO-2025-003', 'ITEM004', 'WH-CLOUD', 100.00, 54.00, 5400.00, 'Pending', 'Pending', '2025-03-10');

-- GL Postings (Finance)
INSERT INTO erp_core_glposting (entry_date, vendor_id, dept_id, cost_center_id, category_id, account_id, amount) VALUES
('2025-01-15', 'V001', 'DEPT-IT', 'CC-IT-01', 'CAT-HW', 'ACC-501', 12500.00),
('2025-02-10', 'V002', 'DEPT-PROD', 'CC-PROD-01', 'CAT-RAW', 'ACC-601', 5000.00),
('2025-03-01', 'V003', 'DEPT-SALES', 'CC-SALES-01', 'CAT-MKT', 'ACC-701', 2000.00);

-- Budgets
INSERT INTO erp_core_budget (cost_center_id, category_id, fiscal_year, fiscal_month, budget_amount) VALUES
('CC-IT-01', 'CAT-HW', 2025, 1, 15000.00),
('CC-IT-02', 'CAT-SW', 2025, 1, 8000.00),
('CC-PROD-01', 'CAT-RAW', 2025, 2, 30000.00),
('CC-SALES-01', 'CAT-MKT', 2025, 3, 5000.00);

-- Approvals
INSERT INTO erp_core_approval (document_type, document_id, role_name, status, created_date, action_date) VALUES
('PO', 'PO-2025-001', 'IT Manager', 'Approved', '2025-01-10', '2025-01-11'),
('PO', 'PO-2025-002', 'Production Head', 'Approved', '2025-02-05', '2025-02-06'),
('PO', 'PO-2025-003', 'IT Director', 'Pending', '2025-03-01', NULL);

-- Default User (demo purposes)
-- Password is 'password123' (plain for demo, but Supabase handles hashing)
INSERT INTO auth_user (username, password, email, name, role) VALUES
('demo', 'password123', 'demo@example.com', 'Demo User', 'Manager');
