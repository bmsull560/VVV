-- Create the models table
CREATE TABLE models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Create the model_components table
CREATE TABLE model_components (
    id VARCHAR(36) PRIMARY KEY,
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    type VARCHAR NOT NULL,
    properties JSONB NOT NULL,
    position JSONB NOT NULL,
    size JSONB
);

-- Create the model_connections table
CREATE TABLE model_connections (
    id VARCHAR(36) PRIMARY KEY,
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    source VARCHAR NOT NULL,
    target VARCHAR NOT NULL,
    sourceHandle VARCHAR,
    targetHandle VARCHAR
);

-- Add trigger to update updated_at column for models table
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$
LANGUAGE plpgsql;

CREATE TRIGGER update_models_updated_at
BEFORE UPDATE ON models
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to update updated_at column for model_components table (if needed, though cascade handles model_id update)
-- CREATE TRIGGER update_model_components_updated_at
-- BEFORE UPDATE ON model_components
-- FOR EACH ROW
-- EXECUTE FUNCTION update_updated_at_column();

-- Add trigger to update updated_at column for model_connections table (if needed)
-- CREATE TRIGGER update_model_connections_updated_at
-- BEFORE UPDATE ON model_connections
-- FOR EACH ROW
-- EXECUTE FUNCTION update_updated_at_column();
