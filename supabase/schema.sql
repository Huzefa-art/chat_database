-- =========================
-- CORE ORGANIZATION
-- =========================

CREATE TABLE IF NOT EXISTS erp_core_legalentity (
    entity_id VARCHAR(20) PRIMARY KEY,
    entity_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS erp_core_department (
    dept_id VARCHAR(20) PRIMARY KEY,
    dept_name VARCHAR(100) NOT NULL,
    entity_id VARCHAR(20) REFERENCES erp_core_legalentity(entity_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS erp_core_costcenter (
    cost_center_code VARCHAR(20) PRIMARY KEY,
    cost_center_name VARCHAR(100) NOT NULL,
    dept_id VARCHAR(20) REFERENCES erp_core_department(dept_id) ON DELETE CASCADE
);

-- =========================
-- VENDOR
-- =========================

CREATE TABLE IF NOT EXISTS erp_core_vendor (
    vendor_code VARCHAR(20) PRIMARY KEY,
    vendor_name VARCHAR(150) NOT NULL,
    vendor_group VARCHAR(100),
    status VARCHAR(20) CHECK (status IN ('Approved', 'Pending', 'Blocked')),
    last_transaction_date DATE
);

CREATE TABLE IF NOT EXISTS erp_core_vendorcontact (
    contact_id SERIAL PRIMARY KEY,
    vendor_id VARCHAR(20) REFERENCES erp_core_vendor(vendor_code) ON DELETE CASCADE,
    contact_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(30),
    is_primary BOOLEAN DEFAULT FALSE
);

-- =========================
-- ITEM
-- =========================

CREATE TABLE IF NOT EXISTS erp_core_item (
    item_code VARCHAR(20) PRIMARY KEY,
    item_name VARCHAR(150) NOT NULL,
    item_group VARCHAR(100),
    unit_of_measure VARCHAR(20),
    reorder_level DECIMAL(18, 2)
);

CREATE TABLE IF NOT EXISTS erp_core_itemvendor (
    id SERIAL PRIMARY KEY,
    item_id VARCHAR(20) REFERENCES erp_core_item(item_code) ON DELETE CASCADE,
    vendor_id VARCHAR(20) REFERENCES erp_core_vendor(vendor_code) ON DELETE CASCADE,
    is_approved BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE,
    last_purchase_price DECIMAL(18, 2),
    UNIQUE (item_id, vendor_id)
);

-- =========================
-- PROCUREMENT
-- =========================

CREATE TABLE IF NOT EXISTS erp_core_purchaseorder (
    po_number VARCHAR(20) PRIMARY KEY,
    vendor_id VARCHAR(20) REFERENCES erp_core_vendor(vendor_code) ON DELETE CASCADE,
    dept_id VARCHAR(20) REFERENCES erp_core_department(dept_id) ON DELETE CASCADE,
    cost_center_id VARCHAR(20) REFERENCES erp_core_costcenter(cost_center_code) ON DELETE SET NULL,
    created_date DATE NOT NULL,
    approved_date DATE,
    status VARCHAR(20) CHECK (status IN ('Draft', 'Pending Approval', 'Approved', 'Received', 'Invoiced')),
    total_value DECIMAL(18, 2)
);

CREATE TABLE IF NOT EXISTS erp_core_purchaseorderline (
    line_id SERIAL PRIMARY KEY,
    po_id VARCHAR(20) REFERENCES erp_core_purchaseorder(po_number) ON DELETE CASCADE,
    item_id VARCHAR(20) REFERENCES erp_core_item(item_code) ON DELETE CASCADE,
    warehouse VARCHAR(50),
    quantity DECIMAL(18, 2) NOT NULL,
    unit_price DECIMAL(18, 2) NOT NULL,
    line_total DECIMAL(18, 2) NOT NULL,
    receipt_status VARCHAR(20),
    invoice_status VARCHAR(20),
    expected_delivery_date DATE
);

CREATE TABLE IF NOT EXISTS erp_core_goodsreceipt (
    receipt_id SERIAL PRIMARY KEY,
    po_line_id INTEGER REFERENCES erp_core_purchaseorderline(line_id) ON DELETE CASCADE,
    received_quantity DECIMAL(18, 2) NOT NULL,
    receipt_date DATE NOT NULL,
    delivery_delay_days INTEGER
);

CREATE TABLE IF NOT EXISTS erp_core_vendorinvoice (
    invoice_id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(30) NOT NULL,
    vendor_id VARCHAR(20) REFERENCES erp_core_vendor(vendor_code) ON DELETE CASCADE,
    po_id VARCHAR(20) REFERENCES erp_core_purchaseorder(po_number) ON DELETE SET NULL,
    invoice_date DATE NOT NULL,
    invoice_amount DECIMAL(18, 2) NOT NULL,
    status VARCHAR(20), -- Posted, Pending, Paid
    due_date DATE
);

-- =========================
-- INVENTORY
-- =========================

CREATE TABLE IF NOT EXISTS erp_core_inventoryonhand (
    inventory_id SERIAL PRIMARY KEY,
    item_id VARCHAR(20) REFERENCES erp_core_item(item_code) ON DELETE CASCADE,
    warehouse VARCHAR(50) NOT NULL,
    quantity_on_hand DECIMAL(18, 2) NOT NULL,
    UNIQUE (item_id, warehouse)
);

CREATE TABLE IF NOT EXISTS erp_core_inventorytransaction (
    transaction_id SERIAL PRIMARY KEY,
    item_id VARCHAR(20) REFERENCES erp_core_item(item_code) ON DELETE CASCADE,
    warehouse VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL, -- Receipt / Issue / Adjustment
    quantity DECIMAL(18, 2) NOT NULL,
    transaction_date DATE NOT NULL,
    reference_type VARCHAR(20),
    reference_id VARCHAR(50)
);

-- =========================
-- FINANCE
-- =========================

CREATE TABLE IF NOT EXISTS erp_core_expenseaccount (
    account_code VARCHAR(20) PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS erp_core_category (
    category_code VARCHAR(20) PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS erp_core_glposting (
    gl_id SERIAL PRIMARY KEY,
    entry_date DATE NOT NULL,
    vendor_id VARCHAR(20) REFERENCES erp_core_vendor(vendor_code) ON DELETE SET NULL,
    dept_id VARCHAR(20) REFERENCES erp_core_department(dept_id) ON DELETE CASCADE,
    cost_center_id VARCHAR(20) REFERENCES erp_core_costcenter(cost_center_code) ON DELETE CASCADE,
    category_id VARCHAR(20) REFERENCES erp_core_category(category_code) ON DELETE SET NULL,
    account_id VARCHAR(20) REFERENCES erp_core_expenseaccount(account_code) ON DELETE CASCADE,
    amount DECIMAL(18, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS erp_core_budget (
    budget_id SERIAL PRIMARY KEY,
    cost_center_id VARCHAR(20) REFERENCES erp_core_costcenter(cost_center_code) ON DELETE CASCADE,
    category_id VARCHAR(20) REFERENCES erp_core_category(category_code) ON DELETE SET NULL,
    fiscal_year INTEGER NOT NULL,
    fiscal_month INTEGER NOT NULL,
    budget_amount DECIMAL(18, 2) NOT NULL
);

-- =========================
-- APPROVALS
-- =========================

CREATE TABLE IF NOT EXISTS erp_core_approval (
    approval_id SERIAL PRIMARY KEY,
    document_type VARCHAR(20) NOT NULL, -- PO, Invoice, etc.
    document_id VARCHAR(50) NOT NULL,
    role_name VARCHAR(50) NOT NULL,
    user_id VARCHAR(50),
    status VARCHAR(20) NOT NULL, -- Pending, Approved, Rejected
    created_date DATE NOT NULL,
    action_date DATE,
    rejection_reason TEXT
);

-- =========================
-- CHAT SYSTEM
-- =========================

CREATE TABLE IF NOT EXISTS auth_user (
    id SERIAL PRIMARY KEY,
    username VARCHAR(150) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    ad_flag BOOLEAN DEFAULT FALSE,
    verified BOOLEAN DEFAULT TRUE,
    organization VARCHAR(255),
    role VARCHAR(100),
    name VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS chat_session (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'New Chat',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_message (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chat_session(id) ON DELETE CASCADE,
    role VARCHAR(10) CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    response_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- HELPER FUNCTIONS
-- =========================

-- Function to execute raw SQL securely for the SQL Agent
CREATE OR REPLACE FUNCTION exec_sql(query_text TEXT)
RETURNS JSONB
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    result JSONB;
BEGIN
    -- Basic security check: only allow SELECT/WITH statements
    IF NOT (UPPER(query_text) LIKE 'SELECT%' OR UPPER(query_text) LIKE 'WITH%') THEN
        RAISE EXCEPTION 'Only SELECT and WITH queries are allowed.';
    END IF;

    EXECUTE 'SELECT json_agg(t) FROM (' || query_text || ') t' INTO result;
    RETURN COALESCE(result, '[]'::jsonB);
END;
$$;
