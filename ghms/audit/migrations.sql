
-- Postgres demo: RLS + WORM for audit_auditlog
ALTER TABLE audit_auditlog ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS audit_select_policy ON audit_auditlog;
CREATE POLICY audit_select_policy ON audit_auditlog FOR SELECT TO ghms_app USING (true);
REVOKE UPDATE, DELETE ON audit_auditlog FROM PUBLIC, ghms_app;
CREATE OR REPLACE FUNCTION prevent_mod_audit() RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'Audit log is append-only';
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS audit_no_update ON audit_auditlog;
CREATE TRIGGER audit_no_update BEFORE UPDATE OR DELETE ON audit_auditlog
  FOR EACH ROW EXECUTE PROCEDURE prevent_mod_audit();
