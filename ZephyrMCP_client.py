#!/usr/bin/env python3
"""
Zephyr Test Management Web Dashboard
A custom web UI that consumes the Zephyr MCP server
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import asyncio
import json
import aiohttp
import os
from datetime import datetime
import plotly.graph_objs as go
import plotly.utils

app = Flask(__name__)

class ZephyrMCPClient:
    """Client to interact with Zephyr MCP Server"""
    
    def __init__(self, mcp_server_url="http://localhost:8000"):
        self.mcp_server_url = mcp_server_url
        
    async def call_tool(self, tool_name, arguments):
        """Call a tool on the MCP server"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            try:
                async with session.post(f"{self.mcp_server_url}/mcp", json=payload) as response:
                    result = await response.json()
                    if 'result' in result:
                        # Extract content from MCP response
                        content = result['result']['content'][0]['text']
                        return json.loads(content)
                    else:
                        return {"error": "No result from MCP server"}
            except Exception as e:
                return {"error": str(e)}

# Initialize MCP client
mcp_client = ZephyrMCPClient()

@app.route('/')
async def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/api/projects')
async def get_projects():
    """Get all projects"""
    result = await mcp_client.call_tool("get_projects", {})
    return jsonify(result)

@app.route('/api/release-status')
async def get_release_status():
    """Get release status for a project"""
    project_id = request.args.get('project_id')
    version_id = request.args.get('version_id')
    
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400
    
    args = {"project_id": project_id}
    if version_id:
        args["version_id"] = version_id
        
    result = await mcp_client.call_tool("get_release_status", args)
    return jsonify(result)

@app.route('/api/test-summary')
async def get_test_summary():
    """Get test execution summary"""
    project_id = request.args.get('project_id')
    version_id = request.args.get('version_id')
    
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400
    
    args = {"project_id": project_id}
    if version_id:
        args["version_id"] = version_id
        
    result = await mcp_client.call_tool("get_test_execution_summary", args)
    return jsonify(result)

@app.route('/api/execution-progress')
async def get_execution_progress():
    """Get execution progress"""
    project_id = request.args.get('project_id')
    version_id = request.args.get('version_id')
    cycle_id = request.args.get('cycle_id')
    
    if not project_id or not version_id:
        return jsonify({"error": "project_id and version_id are required"}), 400
    
    args = {"project_id": project_id, "version_id": version_id}
    if cycle_id:
        args["cycle_id"] = cycle_id
        
    result = await mcp_client.call_tool("get_execution_progress", args)
    return jsonify(result)

@app.route('/api/defects')
async def get_defects():
    """Get defect summary"""
    project_id = request.args.get('project_id')
    version_id = request.args.get('version_id')
    
    if not project_id:
        return jsonify({"error": "project_id is required"}), 400
    
    args = {"project_id": project_id}
    if version_id:
        args["version_id"] = version_id
        
    result = await mcp_client.call_tool("get_defect_summary", args)
    return jsonify(result)

@app.route('/api/regression-tests')
async def get_regression_tests():
    """Get regression test count"""
    project_id = request.args.get('project_id')
    version_id = request.args.get('version_id')
    cycle_name = request.args.get('cycle_name')
    
    if not project_id or not version_id:
        return jsonify({"error": "project_id and version_id are required"}), 400
    
    args = {"project_id": project_id, "version_id": version_id}
    if cycle_name:
        args["cycle_name"] = cycle_name
        
    result = await mcp_client.call_tool("get_regression_test_count", args)
    return jsonify(result)

@app.route('/api/negative-tests')
async def get_negative_tests():
    """Get negative test count"""
    project_id = request.args.get('project_id')
    version_id = request.args.get('version_id')
    
    if not project_id or not version_id:
        return jsonify({"error": "project_id and version_id are required"}), 400
    
    args = {"project_id": project_id, "version_id": version_id}
    result = await mcp_client.call_tool("get_negative_test_count", args)
    return jsonify(result)

@app.route('/api/test-report')
async def generate_test_report():
    """Generate comprehensive test report"""
    project_id = request.args.get('project_id')
    version_id = request.args.get('version_id')
    include_details = request.args.get('include_details', 'false').lower() == 'true'
    
    if not project_id or not version_id:
        return jsonify({"error": "project_id and version_id are required"}), 400
    
    args = {
        "project_id": project_id, 
        "version_id": version_id,
        "include_details": include_details
    }
    result = await mcp_client.call_tool("generate_test_report", args)
    return jsonify(result)

@app.route('/api/charts/execution-progress')
async def chart_execution_progress():
    """Generate execution progress chart data"""
    project_id = request.args.get('project_id')
    version_id = request.args.get('version_id')
    
    if not project_id or not version_id:
        return jsonify({"error": "project_id and version_id are required"}), 400
    
    # Get progress data
    result = await mcp_client.call_tool("get_execution_progress", {
        "project_id": project_id,
        "version_id": version_id
    })
    
    if "error" in result:
        return jsonify(result)
    
    # Prepare chart data
    cycles = []
    passed = []
    failed = []
    blocked = []
    unexecuted = []
    
    for progress in result.get("progress", []):
        cycles.append(progress["cycle"]["name"])
        passed.append(progress["passed"])
        failed.append(progress["failed"])
        blocked.append(progress["blocked"])
        unexecuted.append(progress["unexecuted"])
    
    # Create stacked bar chart
    fig = go.Figure(data=[
        go.Bar(name='Passed', x=cycles, y=passed, marker_color='green'),
        go.Bar(name='Failed', x=cycles, y=failed, marker_color='red'),
        go.Bar(name='Blocked', x=cycles, y=blocked, marker_color='orange'),
        go.Bar(name='Unexecuted', x=cycles, y=unexecuted, marker_color='gray')
    ])
    
    fig.update_layout(
        barmode='stack',
        title='Test Execution Progress by Cycle',
        xaxis_title='Test Cycles',
        yaxis_title='Number of Tests'
    )
    
    return jsonify({
        "chart": json.loads(fig.to_json()),
        "data": result
    })

@app.route('/api/charts/test-distribution')
async def chart_test_distribution():
    """Generate test distribution pie chart"""
    project_id = request.args.get('project_id')
    version_id = request.args.get('version_id')
    
    if not project_id or not version_id:
        return jsonify({"error": "project_id and version_id are required"}), 400
    
    # Get test report
    result = await mcp_client.call_tool("generate_test_report", {
        "project_id": project_id,
        "version_id": version_id,
        "include_details": False
    })
    
    if "error" in result:
        return jsonify(result)
    
    metrics = result.get("overall_metrics", {})
    
    # Create pie chart
    fig = go.Figure(data=[go.Pie(
        labels=['Passed', 'Failed', 'Blocked', 'Unexecuted'],
        values=[
            metrics.get('passed', 0),
            metrics.get('failed', 0),
            metrics.get('blocked', 0),
            metrics.get('unexecuted', 0)
        ],
        marker_colors=['green', 'red', 'orange', 'gray']
    )])
    
    fig.update_layout(title='Test Status Distribution')
    
    return jsonify({
        "chart": json.loads(fig.to_json()),
        "metrics": metrics
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
