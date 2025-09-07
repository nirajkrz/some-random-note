#!/usr/bin/env python3
"""
SmartBear Zephyr Test Management MCP Server
Provides comprehensive test management insights including release status, 
test counts, defects, execution progress, and detailed reporting.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urljoin
import aiohttp
import os
from datetime import datetime, timedelta

# MCP imports
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("zephyr-mcp")

class ZephyrAPIClient:
    """Client for interacting with Zephyr Test Management API"""
    
    def __init__(self, base_url: str, username: str, password: str, access_key: str = None):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.access_key = access_key
        self.session = None
        self.auth_token = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        await self._authenticate()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def _authenticate(self):
        """Authenticate with Zephyr API"""
        try:
            auth_url = f"{self.base_url}/rest/zapi/latest/util/teststep"
            
            # Basic auth or token-based auth depending on setup
            if self.access_key:
                headers = {
                    'Authorization': f'Bearer {self.access_key}',
                    'Content-Type': 'application/json'
                }
            else:
                auth = aiohttp.BasicAuth(self.username, self.password)
                headers = {'Content-Type': 'application/json'}
                
            async with self.session.get(auth_url, headers=headers, auth=auth if not self.access_key else None) as response:
                if response.status == 200:
                    logger.info("Successfully authenticated with Zephyr")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
            
    async def _make_request(self, endpoint: str, method: str = 'GET', params: dict = None, data: dict = None) -> dict:
        """Make authenticated request to Zephyr API"""
        url = f"{self.base_url}/rest/zapi/latest/{endpoint}"
        
        headers = {'Content-Type': 'application/json'}
        if self.access_key:
            headers['Authorization'] = f'Bearer {self.access_key}'
            auth = None
        else:
            auth = aiohttp.BasicAuth(self.username, self.password)
            
        try:
            async with self.session.request(
                method, url, 
                headers=headers, 
                auth=auth,
                params=params, 
                json=data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"API request failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Request to {endpoint} failed: {str(e)}")
            raise
            
    async def get_projects(self) -> List[Dict]:
        """Get all projects"""
        try:
            # This might vary depending on your Zephyr setup
            projects = await self._make_request("util/project")
            return projects if isinstance(projects, list) else list(projects.values())
        except Exception as e:
            logger.error(f"Failed to get projects: {str(e)}")
            return []
            
    async def get_project_versions(self, project_id: str) -> List[Dict]:
        """Get versions/releases for a project"""
        try:
            versions = await self._make_request(f"util/versionBoard-versions/{project_id}")
            return versions if isinstance(versions, list) else list(versions.values())
        except Exception as e:
            logger.error(f"Failed to get versions for project {project_id}: {str(e)}")
            return []
            
    async def get_test_execution_summary(self, project_id: str, version_id: str = None) -> Dict:
        """Get test execution summary for a project/version"""
        try:
            params = {'projectId': project_id}
            if version_id:
                params['versionId'] = version_id
                
            summary = await self._make_request("dashboard/gadget/execution-summary-gadget", params=params)
            return summary
        except Exception as e:
            logger.error(f"Failed to get execution summary: {str(e)}")
            return {}
            
    async def get_cycle_summary(self, project_id: str, version_id: str) -> List[Dict]:
        """Get test cycles for a project version"""
        try:
            params = {
                'projectId': project_id,
                'versionId': version_id
            }
            cycles = await self._make_request("cycle", params=params)
            return cycles if isinstance(cycles, list) else list(cycles.values()) if cycles else []
        except Exception as e:
            logger.error(f"Failed to get cycles: {str(e)}")
            return []
            
    async def get_execution_details(self, project_id: str, version_id: str, cycle_id: str = None) -> List[Dict]:
        """Get detailed execution information"""
        try:
            params = {
                'projectId': project_id,
                'versionId': version_id
            }
            if cycle_id:
                params['cycleId'] = cycle_id
                
            executions = await self._make_request("execution", params=params)
            return executions if isinstance(executions, list) else list(executions.values()) if executions else []
        except Exception as e:
            logger.error(f"Failed to get execution details: {str(e)}")
            return []
            
    async def get_defect_summary(self, project_id: str, version_id: str = None) -> Dict:
        """Get defect summary for a project/version"""
        try:
            params = {'projectId': project_id}
            if version_id:
                params['versionId'] = version_id
                
            defects = await self._make_request("dashboard/gadget/defect-summary-gadget", params=params)
            return defects
        except Exception as e:
            logger.error(f"Failed to get defect summary: {str(e)}")
            return {}

# Initialize the MCP server
server = Server("zephyr-test-management")

# Global client instance
zephyr_client = None

def get_client_config() -> tuple:
    """Get Zephyr configuration from environment variables"""
    base_url = os.getenv('ZEPHYR_BASE_URL', 'https://your-instance.atlassian.net')
    username = os.getenv('ZEPHYR_USERNAME', '')
    password = os.getenv('ZEPHYR_PASSWORD', '')
    access_key = os.getenv('ZEPHYR_ACCESS_KEY', '')
    
    if not username or not password:
        if not access_key:
            raise ValueError("Either ZEPHYR_USERNAME/ZEPHYR_PASSWORD or ZEPHYR_ACCESS_KEY must be provided")
    
    return base_url, username, password, access_key

@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available Zephyr resources"""
    return [
        types.Resource(
            uri="zephyr://projects",
            name="Zephyr Projects",
            description="List all projects in Zephyr",
            mimeType="application/json",
        ),
        types.Resource(
            uri="zephyr://test-summary",
            name="Test Execution Summary",
            description="Get test execution summary by project/version",
            mimeType="application/json",
        ),
        types.Resource(
            uri="zephyr://release-status",
            name="Release Status",
            description="Get comprehensive release status information",
            mimeType="application/json",
        ),
        types.Resource(
            uri="zephyr://defects",
            name="Defect Summary",
            description="Get defect information by project/version",
            mimeType="application/json",
        ),
    ]

@server.read_resource()
async def handle_read_resource(uri: types.AnyUrl) -> str:
    """Read Zephyr resource data"""
    try:
        base_url, username, password, access_key = get_client_config()
        
        async with ZephyrAPIClient(base_url, username, password, access_key) as client:
            if str(uri) == "zephyr://projects":
                projects = await client.get_projects()
                return json.dumps(projects, indent=2)
            else:
                return json.dumps({"error": "Resource not found"}, indent=2)
                
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available Zephyr tools"""
    return [
        types.Tool(
            name="get_projects",
            description="Get all projects from Zephyr",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": [],
            },
        ),
        types.Tool(
            name="get_release_status",
            description="Get comprehensive release status for a project",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "Version/Release ID (optional)"
                    }
                },
                "required": ["project_id"],
            },
        ),
        types.Tool(
            name="get_test_execution_summary",
            description="Get test execution summary with pass/fail counts",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "Version ID (optional)"
                    }
                },
                "required": ["project_id"],
            },
        ),
        types.Tool(
            name="get_regression_test_count",
            description="Get count of regression tests for a project/version",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "Version ID"
                    },
                    "cycle_name": {
                        "type": "string",
                        "description": "Cycle name filter (optional)"
                    }
                },
                "required": ["project_id", "version_id"],
            },
        ),
        types.Tool(
            name="get_negative_test_count",
            description="Get count of negative tests for a project/version",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "Version ID"
                    }
                },
                "required": ["project_id", "version_id"],
            },
        ),
        types.Tool(
            name="get_defect_summary",
            description="Get defect summary for a project/version",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "Version ID (optional)"
                    }
                },
                "required": ["project_id"],
            },
        ),
        types.Tool(
            name="get_execution_progress",
            description="Get detailed test execution progress",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "Version ID"
                    },
                    "cycle_id": {
                        "type": "string",
                        "description": "Cycle ID (optional)"
                    }
                },
                "required": ["project_id", "version_id"],
            },
        ),
        types.Tool(
            name="get_execution_details",
            description="Get detailed execution information for tests",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "Version ID"
                    },
                    "cycle_id": {
                        "type": "string",
                        "description": "Cycle ID (optional)"
                    }
                },
                "required": ["project_id", "version_id"],
            },
        ),
        types.Tool(
            name="generate_test_report",
            description="Generate comprehensive test report for a release",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "string",
                        "description": "Project ID"
                    },
                    "version_id": {
                        "type": "string",
                        "description": "Version ID"
                    },
                    "include_details": {
                        "type": "boolean",
                        "description": "Include detailed execution info (default: false)"
                    }
                },
                "required": ["project_id", "version_id"],
            },
        ),
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    """Handle tool calls"""
    try:
        base_url, username, password, access_key = get_client_config()
        
        async with ZephyrAPIClient(base_url, username, password, access_key) as client:
            
            if name == "get_projects":
                projects = await client.get_projects()
                result = {
                    "projects": projects,
                    "total_count": len(projects),
                    "timestamp": datetime.now().isoformat()
                }
                
            elif name == "get_release_status":
                project_id = arguments["project_id"]
                version_id = arguments.get("version_id")
                
                # Get project versions
                versions = await client.get_project_versions(project_id)
                
                if version_id:
                    selected_versions = [v for v in versions if v.get('id') == version_id]
                else:
                    selected_versions = versions
                    
                release_status = []
                for version in selected_versions:
                    vid = version.get('id', version.get('value'))
                    summary = await client.get_test_execution_summary(project_id, vid)
                    cycles = await client.get_cycle_summary(project_id, vid)
                    
                    release_status.append({
                        "version": version,
                        "execution_summary": summary,
                        "cycles": cycles,
                        "cycle_count": len(cycles)
                    })
                
                result = {
                    "project_id": project_id,
                    "releases": release_status,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif name == "get_test_execution_summary":
                project_id = arguments["project_id"]
                version_id = arguments.get("version_id")
                
                summary = await client.get_test_execution_summary(project_id, version_id)
                
                # Parse and enhance the summary
                result = {
                    "project_id": project_id,
                    "version_id": version_id,
                    "execution_summary": summary,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif name == "get_regression_test_count":
                project_id = arguments["project_id"]
                version_id = arguments["version_id"]
                cycle_name = arguments.get("cycle_name", "")
                
                cycles = await client.get_cycle_summary(project_id, version_id)
                
                # Filter for regression cycles
                regression_cycles = [c for c in cycles if "regression" in c.get('name', '').lower() or 
                                   (cycle_name and cycle_name.lower() in c.get('name', '').lower())]
                
                total_regression_tests = 0
                for cycle in regression_cycles:
                    cycle_id = cycle.get('id')
                    if cycle_id:
                        executions = await client.get_execution_details(project_id, version_id, cycle_id)
                        total_regression_tests += len(executions)
                
                result = {
                    "project_id": project_id,
                    "version_id": version_id,
                    "regression_cycles": regression_cycles,
                    "total_regression_tests": total_regression_tests,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif name == "get_negative_test_count":
                project_id = arguments["project_id"]
                version_id = arguments["version_id"]
                
                executions = await client.get_execution_details(project_id, version_id)
                
                # Count negative tests (tests with "negative" in name or description)
                negative_tests = [e for e in executions if 
                                "negative" in e.get('testCaseName', '').lower() or
                                "negative" in e.get('testCaseDescription', '').lower() or
                                "error" in e.get('testCaseName', '').lower() or
                                "invalid" in e.get('testCaseName', '').lower()]
                
                result = {
                    "project_id": project_id,
                    "version_id": version_id,
                    "negative_test_count": len(negative_tests),
                    "negative_tests": negative_tests,
                    "total_tests": len(executions),
                    "timestamp": datetime.now().isoformat()
                }
                
            elif name == "get_defect_summary":
                project_id = arguments["project_id"]
                version_id = arguments.get("version_id")
                
                defects = await client.get_defect_summary(project_id, version_id)
                
                result = {
                    "project_id": project_id,
                    "version_id": version_id,
                    "defect_summary": defects,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif name == "get_execution_progress":
                project_id = arguments["project_id"]
                version_id = arguments["version_id"]
                cycle_id = arguments.get("cycle_id")
                
                cycles = await client.get_cycle_summary(project_id, version_id)
                progress_data = []
                
                target_cycles = [c for c in cycles if not cycle_id or c.get('id') == cycle_id]
                
                for cycle in target_cycles:
                    cid = cycle.get('id')
                    executions = await client.get_execution_details(project_id, version_id, cid)
                    
                    # Calculate progress metrics
                    total = len(executions)
                    passed = len([e for e in executions if e.get('executionStatus') == 'PASS'])
                    failed = len([e for e in executions if e.get('executionStatus') == 'FAIL'])
                    blocked = len([e for e in executions if e.get('executionStatus') == 'BLOCKED'])
                    unexecuted = len([e for e in executions if e.get('executionStatus') in ['UNEXECUTED', None]])
                    
                    progress_data.append({
                        "cycle": cycle,
                        "total_tests": total,
                        "passed": passed,
                        "failed": failed,
                        "blocked": blocked,
                        "unexecuted": unexecuted,
                        "execution_rate": ((total - unexecuted) / total * 100) if total > 0 else 0,
                        "pass_rate": (passed / total * 100) if total > 0 else 0
                    })
                
                result = {
                    "project_id": project_id,
                    "version_id": version_id,
                    "cycle_id": cycle_id,
                    "progress": progress_data,
                    "timestamp": datetime.now().isoformat()
                }
                
            elif name == "get_execution_details":
                project_id = arguments["project_id"]
                version_id = arguments["version_id"]
                cycle_id = arguments.get("cycle_id")
                
                executions = await client.get_execution_details(project_id, version_id, cycle_id)
                
                result = {
                    "project_id": project_id,
                    "version_id": version_id,
                    "cycle_id": cycle_id,
                    "executions": executions,
                    "total_count": len(executions),
                    "timestamp": datetime.now().isoformat()
                }
                
            elif name == "generate_test_report":
                project_id = arguments["project_id"]
                version_id = arguments["version_id"]
                include_details = arguments.get("include_details", False)
                
                # Gather comprehensive data
                summary = await client.get_test_execution_summary(project_id, version_id)
                cycles = await client.get_cycle_summary(project_id, version_id)
                defects = await client.get_defect_summary(project_id, version_id)
                
                # Calculate overall metrics
                total_tests = 0
                total_passed = 0
                total_failed = 0
                total_blocked = 0
                total_unexecuted = 0
                
                cycle_details = []
                for cycle in cycles:
                    cid = cycle.get('id')
                    executions = await client.get_execution_details(project_id, version_id, cid)
                    
                    cycle_total = len(executions)
                    cycle_passed = len([e for e in executions if e.get('executionStatus') == 'PASS'])
                    cycle_failed = len([e for e in executions if e.get('executionStatus') == 'FAIL'])
                    cycle_blocked = len([e for e in executions if e.get('executionStatus') == 'BLOCKED'])
                    cycle_unexecuted = len([e for e in executions if e.get('executionStatus') in ['UNEXECUTED', None]])
                    
                    total_tests += cycle_total
                    total_passed += cycle_passed
                    total_failed += cycle_failed
                    total_blocked += cycle_blocked
                    total_unexecuted += cycle_unexecuted
                    
                    cycle_detail = {
                        "cycle": cycle,
                        "metrics": {
                            "total": cycle_total,
                            "passed": cycle_passed,
                            "failed": cycle_failed,
                            "blocked": cycle_blocked,
                            "unexecuted": cycle_unexecuted,
                            "execution_rate": ((cycle_total - cycle_unexecuted) / cycle_total * 100) if cycle_total > 0 else 0,
                            "pass_rate": (cycle_passed / cycle_total * 100) if cycle_total > 0 else 0
                        }
                    }
                    
                    if include_details:
                        cycle_detail["executions"] = executions
                        
                    cycle_details.append(cycle_detail)
                
                # Count regression and negative tests
                all_executions = []
                for cycle in cycles:
                    cid = cycle.get('id')
                    execs = await client.get_execution_details(project_id, version_id, cid)
                    all_executions.extend(execs)
                
                regression_count = len([e for e in all_executions if "regression" in e.get('testCaseName', '').lower()])
                negative_count = len([e for e in all_executions if 
                                    "negative" in e.get('testCaseName', '').lower() or
                                    "error" in e.get('testCaseName', '').lower() or
                                    "invalid" in e.get('testCaseName', '').lower()])
                
                result = {
                    "project_id": project_id,
                    "version_id": version_id,
                    "report_generated": datetime.now().isoformat(),
                    "overall_metrics": {
                        "total_tests": total_tests,
                        "passed": total_passed,
                        "failed": total_failed,
                        "blocked": total_blocked,
                        "unexecuted": total_unexecuted,
                        "execution_rate": ((total_tests - total_unexecuted) / total_tests * 100) if total_tests > 0 else 0,
                        "pass_rate": (total_passed / total_tests * 100) if total_tests > 0 else 0,
                        "regression_test_count": regression_count,
                        "negative_test_count": negative_count
                    },
                    "cycle_breakdown": cycle_details,
                    "defect_summary": defects,
                    "execution_summary": summary
                }
            
            else:
                result = {"error": f"Unknown tool: {name}"}
                
        return [types.TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
    except Exception as e:
        error_result = {"error": str(e), "timestamp": datetime.now().isoformat()}
        return [types.TextContent(type="text", text=json.dumps(error_result, indent=2))]

async def main():
    """Main entry point for the MCP server"""
    # Read configuration
    try:
        get_client_config()  # Validate config
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please set the following environment variables:")
        logger.info("- ZEPHYR_BASE_URL (e.g., https://your-instance.atlassian.net)")
        logger.info("- ZEPHYR_USERNAME and ZEPHYR_PASSWORD, OR")
        logger.info("- ZEPHYR_ACCESS_KEY (for token-based auth)")
        return
    
    # Run the server
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="zephyr-test-management",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
