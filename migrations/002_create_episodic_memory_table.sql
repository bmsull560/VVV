-- Function and Trigger to automatically update the 'updated_at' timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- The main table for episodic memory entries
CREATE TABLE episodic_memory_entries (
    -- Base MemoryEntity Fields
    id VARCHAR(36) PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    creator_id VARCHAR(255) NOT NULL,
    sensitivity VARCHAR(50) NOT NULL,
    tier VARCHAR(50) NOT NULL CHECK (tier = 'EPISODIC'),
    ttl INTEGER,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    tags TEXT[] NOT NULL DEFAULT '{}'::text[],
    version INTEGER NOT NULL,
    checksum VARCHAR(64),
    access_policy JSONB,

    -- WorkflowMemoryEntity Fields
    workflow_id VARCHAR(36) NOT NULL,
    workflow_name VARCHAR(255) NOT NULL,
    workflow_status VARCHAR(50) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    user_id VARCHAR(255),
    customer_id VARCHAR(255),
    context_versions TEXT[] NOT NULL DEFAULT '{}'::text[],
    stages JSONB NOT NULL DEFAULT '[]'::jsonb,
    result JSONB,

    -- Constraints
    CONSTRAINT fk_user
        FOREIGN KEY(user_id)
        REFERENCES users(id)
        ON DELETE SET NULL
);

-- Apply the trigger to the table
CREATE TRIGGER update_episodic_memory_entries_updated_at
BEFORE UPDATE ON episodic_memory_entries
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Indexes for performance
CREATE INDEX idx_episodic_workflow_id ON episodic_memory_entries(workflow_id);
CREATE INDEX idx_episodic_user_id ON episodic_memory_entries(user_id);
CREATE INDEX idx_episodic_created_at ON episodic_memory_entries(created_at);
CREATE INDEX idx_episodic_tags ON episodic_memory_entries USING GIN(tags);
CREATE INDEX idx_episodic_metadata ON episodic_memory_entries USING GIN(metadata);
