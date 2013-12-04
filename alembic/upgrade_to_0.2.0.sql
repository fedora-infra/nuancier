-- This upgrade script can be used to upgrade the production database which
-- had only one election and enforce the nullable=False constraint.

-- Update the current election (there is only one in the db)
UPDATE "Elections" SET (election_date_start, election_date_end)
        VALUES ('2013-09-30', '2013-10-04') WHERE "Elections".id == 1

-- Enforce the nullable=False
ALTER TABLE "Elections" ALTER COLUMN election_date_start SET NOT NULL;
ALTER TABLE "Elections" ALTER COLUMN election_date_end SET NOT NULL;
