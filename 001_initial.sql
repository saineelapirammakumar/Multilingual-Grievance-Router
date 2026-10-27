CREATE TABLE grievances (id VARCHAR PRIMARY KEY, token_hash VARCHAR NOT NULL, timestamp VARCHAR NOT NULL, original_text TEXT NOT NULL, language VARCHAR NOT NULL, normalized_text TEXT NOT NULL, prediction TEXT NOT NULL, location TEXT NOT NULL, departments TEXT NOT NULL, urgency VARCHAR NOT NULL, status VARCHAR NOT NULL, assigned_department VARCHAR, resolution TEXT, email VARCHAR, version INTEGER NOT NULL DEFAULT 1);
CREATE TABLE audit_events (id INTEGER PRIMARY KEY, grievance_id VARCHAR NOT NULL REFERENCES grievances(id), timestamp VARCHAR NOT NULL, actor VARCHAR NOT NULL, kind VARCHAR NOT NULL, payload TEXT NOT NULL);
CREATE TABLE notifications (id INTEGER PRIMARY KEY, grievance_id VARCHAR NOT NULL REFERENCES grievances(id), timestamp VARCHAR NOT NULL, message TEXT NOT NULL, delivery VARCHAR NOT NULL, attempts INTEGER NOT NULL DEFAULT 0);
CREATE TABLE duplicates (first_id VARCHAR NOT NULL REFERENCES grievances(id), second_id VARCHAR NOT NULL REFERENCES grievances(id), actor VARCHAR NOT NULL, note TEXT NOT NULL, PRIMARY KEY(first_id,second_id));
CREATE INDEX ix_grievances_status ON grievances(status);
CREATE INDEX ix_grievances_urgency ON grievances(urgency);
CREATE INDEX ix_audit_grievance ON audit_events(grievance_id);
CREATE INDEX ix_notification_grievance ON notifications(grievance_id);
