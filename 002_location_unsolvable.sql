ALTER TABLE grievances ADD COLUMN is_unsolvable BOOLEAN NOT NULL DEFAULT 0;
ALTER TABLE grievances ADD COLUMN unsolvable_reason TEXT;
ALTER TABLE grievances ADD COLUMN unsolvable_by VARCHAR;
ALTER TABLE grievances ADD COLUMN unsolvable_at VARCHAR;
CREATE INDEX ix_grievances_unsolvable ON grievances(is_unsolvable);
