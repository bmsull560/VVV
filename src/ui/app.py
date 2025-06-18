import os
import sys
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS

from ..agents.intake_assistant.main import IntakeAssistantAgent
from ..agents.roi_calculator.main import ROICalculatorAgent
from ..agents.data_correlator.main import DataCorrelatorAgent
from ..memory.mcp_client import MCPClient
from ..memory.semantic_memory import SemanticMemory
from ..memory.storage.postgres_storage import PostgresStorage
from ..memory.types import to_dict # Import the utility to serialize entities

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}}) # Allow CORS for API routes from the React app
app.secret_key = os.urandom(24)

# --- MCP and Agent Setup ---
storage_backend = None
DSN = os.getenv("TEST_POSTGRES_DSN")
if DSN:
    storage_backend = PostgresStorage(dsn=DSN)
    # In a real application, this would be part of a startup script
    try:
        asyncio.run(storage_backend.initialize())
    except Exception as e:
        print(f"Error initializing PostgreSQL storage: {e}")
        storage_backend = None

mcp_client = MCPClient(memory=SemanticMemory(storage_backend=storage_backend))
intake_agent = IntakeAssistantAgent(agent_id="ui-intake-agent", mcp_client=mcp_client, config={})
roi_agent = ROICalculatorAgent(agent_id="ui-roi-agent", mcp_client=mcp_client, config={})
correlator_agent = DataCorrelatorAgent(agent_id="ui-correlator-agent", mcp_client=mcp_client, config={})

@app.route('/api/start-analysis', methods=['POST'])
async def start_analysis():
    """Starts a new analysis task by running the Intake Assistant Agent."""
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    if not storage_backend:
        return jsonify({'error': 'Storage backend not initialized'}), 500

    try:
        # In a real application, this agent would run in a background task queue.
        # For this implementation, we'll run it asynchronously.
        # We assume the agent has an async `run` method.
        result = await intake_agent.run(data['content'])

        # The result from the agent is stored as a 'project_intake' entity.
        # The entity ID can be used to track the analysis workflow.
        entity_id = result.id

        return jsonify({'id': entity_id}), 202  # Accepted
    except Exception as e:
        print(f"Error during analysis start: {e}") # Basic logging
        return jsonify({'error': 'Failed to start analysis task.'}), 500

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Returns a list of all submitted projects."""
    projects = []
    if storage_backend:
        try:
            all_entities = asyncio.run(mcp_client.memory.storage.get_all())
            # Filter for entities created by the intake agent and serialize them
            project_entities = [e for e in all_entities if e.metadata.get('source') == 'IntakeAssistantAgent']
            projects = [to_dict(p) for p in project_entities]
        except Exception as e:
            return jsonify({'error': f'Could not load projects: {e}'}), 500
    return jsonify(projects)

@app.route('/api/calculate_roi', methods=['POST'])
def calculate_roi():
    """Handles the ROI calculation and returns JSON."""
    data = request.get_json()
    if not data or 'investment' not in data or 'gain' not in data:
        return jsonify({'error': 'Missing investment or gain in request body'}), 400

    try:
        result = asyncio.run(roi_agent.execute(data))
        if result.status.is_completed():
            return jsonify(result.data)
        else:
            return jsonify({'error': result.data.get('error', 'Unknown ROI calculation error')}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/correlate_data', methods=['POST'])
def correlate_data():
    """Handles data correlation and returns JSON."""
    data = request.get_json()
    if not data or 'dataset1' not in data or 'dataset2' not in data:
        return jsonify({'error': 'Missing dataset1 or dataset2 in request body'}), 400

    try:
        result = asyncio.run(correlator_agent.execute(data))
        if result.status.is_completed():
            return jsonify(result.data)
        else:
            return jsonify({'error': result.data.get('error', 'Unknown correlation error')}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/submit', methods=['POST'])
def submit():
    """Handles the project intake form submission from the API."""
    data = request.get_json()
    if not data or not all(k in data for k in ['project_name', 'description', 'goals']):
        return jsonify({'error': 'Missing required fields: project_name, description, goals'}), 400

    try:
        result = asyncio.run(intake_agent.execute(data))
        if result.status.is_completed():
            return jsonify({'message': 'Project submitted successfully!', 'entity_id': result.data.get('entity_id')}), 201
        else:
            return jsonify({'error': result.data.get('error', 'Unknown error during project intake')}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500
