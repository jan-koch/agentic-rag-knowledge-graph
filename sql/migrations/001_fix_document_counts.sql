-- Migration: Fix document counts for all workspaces
-- This updates the document_count field for all existing workspaces
-- and adds a trigger to keep it updated automatically

-- Update all existing workspaces with correct document counts
UPDATE workspaces
SET document_count = (
    SELECT COUNT(*)
    FROM documents
    WHERE documents.workspace_id = workspaces.id
);

-- Create function to automatically update workspace document count
CREATE OR REPLACE FUNCTION update_workspace_document_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE workspaces
        SET document_count = document_count + 1
        WHERE id = NEW.workspace_id;
        RETURN NEW;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE workspaces
        SET document_count = GREATEST(0, document_count - 1)
        WHERE id = OLD.workspace_id;
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger (drop if exists first)
DROP TRIGGER IF EXISTS update_document_count_trigger ON documents;
CREATE TRIGGER update_document_count_trigger
    AFTER INSERT OR DELETE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION update_workspace_document_count();

-- Verify counts are correct
SELECT
    w.id,
    w.name,
    w.document_count,
    COUNT(d.id) AS actual_count,
    CASE
        WHEN w.document_count = COUNT(d.id) THEN 'OK'
        ELSE 'MISMATCH'
    END AS status
FROM workspaces w
LEFT JOIN documents d ON d.workspace_id = w.id
GROUP BY w.id, w.name, w.document_count
ORDER BY w.name;
