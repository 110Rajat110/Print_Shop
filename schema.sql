CREATE TABLE IF NOT EXISTS PrintBatches (
  batch_id INTEGER PRIMARY KEY AUTOINCREMENT,
  mobile_number TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'Waiting',
  total_cost REAL NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS PrintFiles (
  file_id INTEGER PRIMARY KEY AUTOINCREMENT,
  batch_id INTEGER NOT NULL,
  file_name_original TEXT NOT NULL,
  file_path_saved TEXT NOT NULL,
  page_count_original INTEGER NOT NULL,
  page_range TEXT NOT NULL DEFAULT 'All',
  page_count_final INTEGER NOT NULL,
  copies INTEGER NOT NULL DEFAULT 1,
  print_color INTEGER NOT NULL DEFAULT 0,
  print_duplex INTEGER NOT NULL DEFAULT 0,
  file_cost REAL NOT NULL,
  FOREIGN KEY(batch_id) REFERENCES PrintBatches(batch_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Settings (
  setting_key TEXT PRIMARY KEY,
  setting_value REAL NOT NULL
);

INSERT OR IGNORE INTO Settings (setting_key, setting_value)
VALUES
  ('price_per_page_bw', 2.00),
  ('price_per_page_color', 10.00),
  ('price_duplex_multiplier', 1.8);
