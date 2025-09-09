-- Fix for production database enum issue
-- Run this SQL script on your production database before running alembic upgrade

-- Create the enum type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'itinerarytypeenum') THEN
        CREATE TYPE itinerarytypeenum AS ENUM ('TREK', 'CITY_TOUR', 'MIXED');
    END IF;
END
$$;

-- Verify the enum was created
SELECT enumlabel FROM pg_enum WHERE enumtypid = (
    SELECT oid FROM pg_type WHERE typname = 'itinerarytypeenum'
);
