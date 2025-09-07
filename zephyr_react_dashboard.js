import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';
import { Bar, Pie } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

// MCP Client Hook
const useMCPClient = () => {
  const callTool = async (toolName, arguments) => {
    try {
      const response = await fetch('/api/mcp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          method: 'tools/call',
          params: {
            name: toolName,
            arguments: arguments
          }
        })
      });
      
      const result = await response.json();
      if (result.result && result.result.content) {
        return JSON.parse(result.result.content[0].text);
      }
      throw new Error('Invalid response from MCP server');
    } catch (error) {
      console.error('MCP call failed:', error);
      throw error;
    }
  };

  return { callTool };
};

// Metric Card Component
const MetricCard = ({ title, value, icon, color = 'blue', subtitle = '' }) => (
  <div className={`bg-white rounded-lg shadow-md p-6 border-l-4 border-${color}-500`}>
    <div className="flex items-center justify-between">
      <div>
        <h3 className="text-lg font-semibold text-gray-700">{title}</h3>
        <p className={`text-3xl font-bold text-${color}-600 mt-2`}>{value}</p>
        {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
      </div>
      <div className={`text-${color}-500 text-4xl`}>
        <i className={icon}></i>
      </div>
    </div>
  </div>
);

// Progress Bar Component
const ProgressBar = ({ label, value, total, color = 'blue' }) => {
  const percentage = total > 0 ? (value / total) * 100 : 0;
  
  return (
    <div className="mb-4">
      <div className="flex justify-between items-center mb-2">
        <span className="text-sm font-medium text-gray-700">{label}</span>
        <span className="text-sm text-gray-500">{value}/{total} ({percentage.toFixed(1)}%)</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`bg-${color}-500 h-2 rounded-full transition-all duration-300`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );
};

// Cycle Card Component
const CycleCard = ({ cycle }) => {
  const total = cycle.total_tests;
  const executionRate = cycle.execution_rate || 0;
  const passRate = cycle.pass_rate || 0;

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h4 className="text-xl font-semibold text-gray-800">{cycle.cycle.name}</h4>
          <p className="text-gray-600">{cycle.cycle.description}</p>
        </div>
        <div className="text-right">
          <span className="text-2xl font-bold text-gray-800">{total}</span>
          <p className="text-sm text-gray-500">Total Tests</p>
        </div>
      </div>
      
      <div className="grid grid-cols-4 gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{cycle.passed}</div>
          <div className="text-sm text-gray-600">Passed</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{cycle.failed}</div>
          <div className="text-sm text-gray-600">Failed</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-yellow-600">{cycle.blocked}</div>
          <div className="text-sm text-gray-600">Blocked</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-600">{cycle.unexecuted}</div>
          <div className="text-sm text-gray-600">Pending</div>
        </div>
      </div>
      
      <div className="space-y-2">
        <ProgressBar 
          label="Execution Progress" 
          value={total - cycle.unexecuted} 
          total={total} 
          color="blue" 
        />
        <ProgressBar 
          label="Pass Rate" 
          value={cycle.passed} 
          total={total} 
          color="green" 
        />
      </div>
    </div>
  );
};

// Loading Component
const LoadingSpinner = () => (
  <div className="flex justify-center items-center h-64">
    <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
    <span className="ml-4 text-lg text-gray-600">Loading Zephyr data...</span>
  </div>
);

// Main Dashboard Component
const ZephyrDashboard = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [selectedVersion, setSelectedVersion] = useState('');
  const [versions, setVersions] = useState([]);
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const { callTool } = useMCPClient();

  // Load projects on component mount
  useEffect(() => {
    loadProjects();
  }, []);

  // Load versions when project changes
  useEffect(() => {
    if (selectedProject) {
      loadVersions(selectedProject);
    }
  }, [selectedProject]);

  // Load dashboard when both project and version are selected
  useEffect(() => {
    if (selectedProject && selectedVersion) {
      loadDashboard();
    }
  }, [selectedProject, selectedVersion]);

  const loadProjects = async () => {
    try {
      const result = await callTool('get_projects', {});
      if (result.error) {
        setError(result.error);
      } else {
        setProjects(result.projects || []);
      }
    } catch (err) {
      setError('Failed to load projects: ' + err.message);
    }
  };

  const loadVersions = async (projectId) => {
    try {
      const result = await callTool('get_release_status', { project_id: projectId });
      if (result.error) {
        setError(result.error);
      } else {
        const versionList = result.releases?.map(r => r.version) || [];
        setVersions(versionList);
      }
    } catch (err) {
      setError('Failed to load versions: ' + err.message);
    }
  };

  const loadDashboard = async () => {
    setLoading(true);
    setError('');

    try {
      // Load all required data in parallel
      const [report, progress, regressionTests, negativeTests] = await Promise.all([
        callTool('generate_test_report', {
          project_id: selectedProject,
          version_id: selectedVersion,
          include_details: false
        }),
        callTool('get_execution_progress', {
          project_id: selectedProject,
          version_id: selectedVersion
        }),
        callTool('get_regression_test_count', {
          project_id: selectedProject,
          version_id: selectedVersion
        }),
        callTool('get_negative_test_count', {
          project_id: selectedProject,
          version_id: selectedVersion
        })
      ]);

      setDashboardData({
        report,
        progress,
        regressionTests,
        negativeTests
      });
    } catch (err) {
      setError('Failed to load dashboard: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const refreshDashboard = () => {
    if (selectedProject && selectedVersion) {
      loadDashboard();
    }
  };

  // Prepare chart data
  const getExecutionChartData = () => {
    if (!dashboardData?.progress?.progress) return null;

    const cycles = dashboardData.progress.progress;
    
    return {
      labels: cycles.map(c => c.cycle.name),
      datasets: [
        {
          label: 'Passed',
          data: cycles.map(c => c.passed),
          backgroundColor: 'rgba(34, 197, 94, 0.8)',
          borderColor: 'rgba(34, 197, 94, 1)',
          borderWidth: 1
        },
        {
          label: 'Failed',
          data: cycles.map(c => c.failed),
          backgroundColor: 'rgba(239, 68, 68, 0.8)',
          borderColor: 'rgba(239, 68, 68, 1)',
          borderWidth: 1
        },
        {
          label: 'Blocked',
          data: cycles.map(c => c.blocked),
          backgroundColor: 'rgba(245, 158, 11, 0.8)',
          borderColor: 'rgba(245, 158, 11, 1)',
          borderWidth: 1
        },
        {
          label: 'Unexecuted',
          data: cycles.map(c => c.unexecuted),
          backgroundColor: 'rgba(107, 114, 128, 0.8)',
          borderColor: 'rgba(107, 114, 128, 1)',
          borderWidth: 1
        }
      ]
    };
  };

  const getDistributionChartData = () => {
    if (!dashboardData?.report?.overall_metrics) return null;

    const metrics = dashboardData.report.overall_metrics;
    
    return {
      labels: ['Passed', 'Failed', 'Blocked', 'Unexecuted'],
      datasets: [{
        data: [metrics.passed, metrics.failed, metrics.blocked, metrics.unexecuted],
        backgroundColor: [
          'rgba(34, 197, 94, 0.8)',
          'rgba(239, 68, 68, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(107, 114, 128, 0.8)'
        ],
        borderColor: [
          'rgba(34, 197, 94, 1)',
          'rgba(239, 68, 68, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(107, 114, 128, 1)'
        ],
        borderWidth: 2
      }]
    };
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top',
      },
    },
    scales: {
      x: {
        stacked: true,
      },
      y: {
        stacked: true,
      },
    },
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <i className="fas fa-bug-slash text-3xl text-blue-600 mr-3"></i>
              <h1 className="text-3xl font-bold text-gray-900">Zephyr Test Dashboard</h1>
            </div>
            
            <div className="flex space-x-4">
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Select Project</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.key} - {project.name}
                  </option>
                ))}
              </select>
              
              <select
                value={selectedVersion}
                onChange={(e) => setSelectedVersion(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={!versions.length}
              >
                <option value="">Select Version</option>
                {versions.map(version => (
                  <option key={version.id} value={version.id}>
                    {version.name}
                  </option>
                ))}
              </select>
              
              <button
                onClick={refreshDashboard}
                disabled={!selectedProject || !selectedVersion || loading}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <i className="fas fa-sync-alt mr-2"></i>
                Refresh
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading ? (
          <LoadingSpinner />
        ) : dashboardData ? (
          <>
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <MetricCard
                title="Total Tests"
                value={dashboardData.report.overall_metrics?.total_tests || 0}
                icon="fas fa-list-check"
                color="blue"
              />
              <MetricCard
                title="Execution Rate"
                value={`${(dashboardData.report.overall_metrics?.execution_rate || 0).toFixed(1)}%`}
                icon="fas fa-play-circle"
                color="indigo"
              />
              <MetricCard
                title="Pass Rate"
                value={`${(dashboardData.report.overall_metrics?.pass_rate || 0).toFixed(1)}%`}
                icon="fas fa-check-circle"
                color="green"
              />
              <MetricCard
                title="Open Defects"
                value={dashboardData.report.defect_summary?.openDefects || 0}
                icon="fas fa-exclamation-triangle"
                color="red"
              />
            </div>

            {/* Test Type Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
              <MetricCard
                title="Regression Tests"
                value={dashboardData.regressionTests?.total_regression_tests || 0}
                icon="fas fa-redo"
                color="yellow"
                subtitle="Automated regression suite"
              />
              <MetricCard
                title="Negative Tests"
                value={dashboardData.negativeTests?.negative_test_count || 0}
                icon="fas fa-times-circle"
                color="purple"
                subtitle="Error handling tests"
              />
              <MetricCard
                title="Test Cycles"
                value={dashboardData.report.cycle_breakdown?.length || 0}
                icon="fas fa-sync"
                color="teal"
                subtitle="Active test cycles"
              />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              {/* Execution Progress Chart */}
              <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">
                  <i className="fas fa-chart-bar mr-2"></i>
                  Execution Progress by Cycle
                </h3>
                <div className="h-80">
                  {getExecutionChartData() && (
                    <Bar data={getExecutionChartData()} options={chartOptions} />
                  )}
                </div>
              </div>

              {/* Distribution Chart */}
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">
                  <i className="fas fa-chart-pie mr-2"></i>
                  Test Status Distribution
                </h3>
                <div className="h-80">
                  {getDistributionChartData() && (
                    <Pie data={getDistributionChartData()} options={pieOptions} />
                  )}
                </div>
              </div>
            </div>

            {/* Cycle Details */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-6">
                <i className="fas fa-tasks mr-2"></i>
                Cycle Details
              </h3>
              <div className="space-y-4">
                {dashboardData.progress?.progress?.map((cycle, index) => (
                  <CycleCard key={index} cycle={cycle} />
                ))}
              </div>
            </div>
          </>
        ) : (
          <div className="text-center py-16">
            <i className="fas fa-chart-line text-6xl text-gray-400 mb-4"></i>
            <h2 className="text-2xl font-semibold text-gray-600 mb-2">Welcome to Zephyr Dashboard</h2>
            <p className="text-gray-500">Select a project and version to view test management insights</p>
          </div>
        )}
      </main>
    </div>
  );
};

export default ZephyrDashboard;