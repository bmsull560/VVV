import os
import sys
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS

# Agent Imports
from agents.intake_assistant.main import IntakeAssistantAgent
from agents.roi_calculator.main import ROICalculatorAgent
from agents.data_correlator.main import DataCorrelatorAgent
from agents.value_driver.main import ValueDriverAgent
from agents.persona.main import PersonaAgent
from agents.sensitivity_analysis.main import SensitivityAnalysisAgent

# Memory and Storage Imports
from memory.mcp_client import MCPClient
from memory.semantic_memory import SemanticMemory
from memory.storage.postgres_storage import PostgresStorage
from memory.types import to_dict

app = Flask(__name__)
# In a real app, this should be more restrictive. For dev, we allow the React dev server.
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:5173", "http://localhost:5174"]}})
app.secret_key = os.urandom(24)

# --- MCP and Agent Setup ---
storage_backend = None
DSN = os.getenv("TEST_POSTGRES_DSN")
if DSN:
    try:
        storage_backend = PostgresStorage(dsn=DSN)
        asyncio.run(storage_backend.initialize())
        print("PostgreSQL storage initialized successfully.")
    except Exception as e:
        print(f"Error initializing PostgreSQL storage: {e}", file=sys.stderr)
        storage_backend = None
else:
    print("Warning: TEST_POSTGRES_DSN not set. Using in-memory storage.", file=sys.stderr)

mcp_client = MCPClient(memory=SemanticMemory(storage_backend=storage_backend))

# Instantiate all agents
intake_agent = IntakeAssistantAgent(agent_id="intake_assistant", mcp_client=mcp_client, config={})
roi_agent = ROICalculatorAgent(agent_id="roi_calculator", mcp_client=mcp_client, config={})
correlator_agent = DataCorrelatorAgent(agent_id="data_correlator", mcp_client=mcp_client, config={})
value_driver_agent = ValueDriverAgent(agent_id="value_driver", mcp_client=mcp_client, config={})
persona_agent = PersonaAgent(agent_id="persona", mcp_client=mcp_client, config={})
sensitivity_agent = SensitivityAnalysisAgent(agent_id="sensitivity_analysis", mcp_client=mcp_client, config={})

# --- API Endpoints ---

@app.route('/api/start-analysis', methods=['POST'])
async def start_analysis():
    """Starts a new analysis task by running the Intake Assistant Agent."""
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({'error': 'Invalid input'}), 400

    if not storage_backend:
        return jsonify({'error': 'Storage backend not initialized'}), 500

    try:
        # The Intake agent's 'run' method creates and stores an entity.
        result_entity = await intake_agent.run(data['content'])
        return jsonify({'id': result_entity.id}), 202  # Accepted
    except Exception as e:
        print(f"Error during analysis start: {e}", file=sys.stderr)
        return jsonify({'error': 'Failed to start analysis task.'}), 500

@app.route('/api/discover-value/<entity_id>', methods=['POST'])
async def discover_value(entity_id):
    """
    Takes an entity ID from the intake process and runs the Value Driver
    and Persona agents to discover key insights.
    """
    if not storage_backend:
        return jsonify({'error': 'Storage backend not initialized'}), 500

    try:
        intake_entity = await mcp_client.memory.storage.get(entity_id)
        if not intake_entity:
            return jsonify({'error': 'Project entity not found'}), 404

        input_text = intake_entity.data.get('text')
        if not input_text:
            return jsonify({'error': 'No text found in the intake entity to analyze'}), 400

        # Run ValueDriver and Persona agents in parallel
        value_driver_task = value_driver_agent.execute({'text': input_text})
        persona_task = persona_agent.execute({'text': input_text})
        driver_result, persona_result = await asyncio.gather(value_driver_task, persona_task)

        if driver_result.status.is_failed() or persona_result.status.is_failed():
            return jsonify({
                'error': 'One or more analysis agents failed.',
                'details': {
                    'value_driver': driver_result.data,
                    'persona': persona_result.data
                }
            }), 500
            
        combined_results = {
            'value_drivers': driver_result.data.get('drivers', []),
            'personas': persona_result.data.get('personas', [])
        }

        return jsonify(combined_results), 200

    except Exception as e:
        print(f"Error during value discovery: {e}", file=sys.stderr)
        return jsonify({'error': 'Failed to perform value discovery.'}), 500

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Returns a list of all submitted projects."""
    projects = []
    if storage_backend:
        try:
            all_entities = asyncio.run(mcp_client.memory.storage.get_all())
            project_entities = [e for e in all_entities if e.metadata.get('source') == 'IntakeAssistantAgent']
            projects = [to_dict(p) for p in project_entities]
        except Exception as e:
            return jsonify({'error': f'Could not load projects: {e}'}), 500
    return jsonify(projects)

@app.route('/api/calculate_roi', methods=['POST'])
async def calculate_roi():
    """Handles the ROI calculation and returns JSON."""
    data = request.get_json()
    if not data or 'investment' not in data or 'gain' not in data:
        return jsonify({'error': 'Missing investment or gain in request body'}), 400

    try:
        result = await roi_agent.execute(data)
        if result.status.is_completed():
            return jsonify(result.data)
        else:
            return jsonify({'error': result.data.get('error', 'Unknown ROI calculation error')}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/correlate_data', methods=['POST'])
async def correlate_data():
    """Handles data correlation and returns JSON."""
    data = request.get_json()
    if not data or 'dataset1' not in data or 'dataset2' not in data:
        return jsonify({'error': 'Missing dataset1 or dataset2 in request body'}), 400

    try:
        result = await correlator_agent.execute(data)
        if result.status.is_completed():
            return jsonify(result.data)
        else:
            return jsonify({'error': result.data.get('error', 'Unknown correlation error')}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

@app.route('/api/run-sensitivity-analysis', methods=['POST'])
async def run_sensitivity_analysis():
    """Runs the sensitivity analysis agent and returns the results."""
    data = request.get_json()
    if not data or 'base_investment' not in data or 'base_gain' not in data or 'variations' not in data:
        return jsonify({'error': 'Invalid input. Requires base_investment, base_gain, and variations.'}), 400

    try:
        result = await sensitivity_agent.execute(data)
        if result.status.is_completed():
            return jsonify(result.data)
        else:
            return jsonify({'error': result.data.get('error', 'Unknown sensitivity analysis error')}), 400
    except Exception as e:
        return jsonify({'error': f'An unexpected error occurred: {str(e)}'}), 500

