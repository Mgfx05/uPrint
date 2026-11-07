-- uPrint cloud foundation: file metadata and customer orders
CREATE TABLE IF NOT EXISTS files (
  file_id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  page_count INTEGER NOT NULL,
  file_size_bytes INTEGER NOT NULL,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  expires_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id TEXT NOT NULL UNIQUE,
  file_id TEXT NOT NULL,
  pages INTEGER NOT NULL,
  copies INTEGER NOT NULL CHECK (copies BETWEEN 1 AND 50),
  print_type TEXT NOT NULL CHECK (print_type IN ('bw', 'color')),
  paper_size TEXT NOT NULL CHECK (paper_size IN ('a4', 'a3')),
  sides TEXT NOT NULL CHECK (sides IN ('single', 'double')),
  orientation TEXT NOT NULL CHECK (orientation IN ('portrait', 'landscape')),
  amount REAL NOT NULL,
  payment_status TEXT NOT NULL DEFAULT 'pending',
  print_status TEXT NOT NULL DEFAULT 'queued',
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  FOREIGN KEY (file_id) REFERENCES files(file_id)
);

CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);
CREATE INDEX IF NOT EXISTS idx_orders_print_status ON orders(print_status, id);
