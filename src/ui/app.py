import os
import sys
import asyncio
from flask import Flask, render_template, request, redirect, url_for, flash

from ..agents.intake_assistant.main import IntakeAssistantAgent
from ..agents.roi_calculator.main import ROICalculatorAgent
from ..agents.data_correlator.main import DataCorrelatorAgent
from ..memory.mcp_client import MCPClient
from ..memory.semantic_memory import SemanticMemory
from ..memory.storage.postgres_storage import PostgresStorage

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Securely generate a secret key

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

@app.route('/')
def index():
    """Renders the main project intake form."""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Renders the main dashboard, showing projects and providing tools."""
    projects = []
    if storage_backend:
        try:
            # This is a simplified fetch. A real app would have more robust querying.
            all_entities = asyncio.run(mcp_client.memory.storage.get_all())
            projects = [e for e in all_entities if e.metadata.get('source') == 'IntakeAssistant']
        except Exception as e:
            flash(f"Could not load projects: {e}", 'error')
    return render_template('dashboard.html', projects=projects)

@app.route('/calculate_roi', methods=['POST'])
def calculate_roi():
    """Handles the ROI calculation form submission."""
    investment = request.form.get('investment')
    gain = request.form.get('gain')
    inputs = {'investment': investment, 'gain': gain}

    try:
        result = asyncio.run(roi_agent.execute(inputs))
        if result.status.is_completed():
            flash(f"Calculated ROI: {result.data['roi_percentage']}%", 'success')
        else:
            flash(f"ROI Calculation Error: {result.data.get('error')}", 'error')
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/correlate_data', methods=['POST'])
def correlate_data():
    """Handles the data correlation form submission."""
    try:
        dataset1 = [float(x) for x in request.form.get('dataset1', '').split(',') if x.strip()]
        dataset2 = [float(x) for x in request.form.get('dataset2', '').split(',') if x.strip()]
    except ValueError:
        flash("Datasets must contain comma-separated numbers only.", 'error')
        return redirect(url_for('dashboard'))

    inputs = {'dataset1': dataset1, 'dataset2': dataset2}
    try:
        result = asyncio.run(correlator_agent.execute(inputs))
        if result.status.is_completed():
            flash(f"Correlation Coefficient: {result.data['correlation_coefficient']}", 'success')
        else:
            flash(f"Correlation Error: {result.data.get('error')}", 'error')
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", 'error')

    return redirect(url_for('dashboard'))


@app.route('/submit', methods=['POST'])
def submit():
    """Handles the form submission and executes the IntakeAssistantAgent."""
    project_name = request.form.get('project_name')
    description = request.form.get('description')
    goals = request.form.get('goals')

    if not all([project_name, description, goals]):
        flash('All fields are required!', 'error')
        return redirect(url_for('index'))

    goals_list = [goal.strip() for goal in goals.splitlines() if goal.strip()]

    inputs = {
        "project_name": project_name,
        "description": description,
        "goals": goals_list
    }

    try:
        result = asyncio.run(intake_agent.execute(inputs))
        if result.status.is_completed():
            flash(f"Project '{project_name}' submitted successfully!", 'success')
        else:
            flash(f"Error submitting project: {result.data.get('error', 'Unknown error')}", 'error')
    except Exception as e:
        flash(f"An unexpected error occurred: {str(e)}", 'error')

    return redirect(url_for('index'))

# This application is designed to be run from the root `run.py` script.
