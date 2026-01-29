'use client';

import { useEffect, useState, useCallback } from 'react';
import { Octokit } from '@octokit/rest';
import { formatDistanceToNow } from 'date-fns';
import {
  Shield,
  ShieldAlert,
  ShieldCheck,
  Activity,
  Terminal,
  GitCommit,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Zap,
  Eye,
} from 'lucide-react';

// Types
interface WorkflowRun {
  id: number;
  name: string;
  head_sha: string;
  head_commit: {
    message: string;
    author: {
      name: string;
      email: string;
    };
    timestamp: string;
  } | null;
  conclusion: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  html_url: string;
  head_branch: string;
  actor: {
    login: string;
    avatar_url: string;
  } | null;
}

interface Stats {
  totalScans: number;
  blocked: number;
  approved: number;
  blockRate: number;
  inProgress: number;
}

// Configuration
const GITHUB_TOKEN = process.env.NEXT_PUBLIC_GITHUB_TOKEN || '';
const OWNER = process.env.NEXT_PUBLIC_GITHUB_OWNER || '';
const REPO = process.env.NEXT_PUBLIC_GITHUB_REPO || '';

export default function OpsGuardMonitor() {
  const [runs, setRuns] = useState<WorkflowRun[]>([]);
  const [stats, setStats] = useState<Stats>({
    totalScans: 0,
    blocked: 0,
    approved: 0,
    blockRate: 0,
    inProgress: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [bootSequence, setBootSequence] = useState(true);

  const fetchWorkflowRuns = useCallback(async () => {
    if (!GITHUB_TOKEN || !OWNER || !REPO) {
      setError('Configuration missing. Check your .env.local file.');
      setLoading(false);
      setBootSequence(false);
      return;
    }

    try {
      const octokit = new Octokit({ auth: GITHUB_TOKEN });

      const { data } = await octokit.rest.actions.listWorkflowRunsForRepo({
        owner: OWNER,
        repo: REPO,
        per_page: 50,
      });

      const workflowRuns = data.workflow_runs as WorkflowRun[];
      setRuns(workflowRuns);

      // Calculate stats based on business logic:
      // failure = BLOCKED by OpsGuard
      // success = APPROVED
      const blocked = workflowRuns.filter((r) => r.conclusion === 'failure').length;
      const approved = workflowRuns.filter((r) => r.conclusion === 'success').length;
      const inProgress = workflowRuns.filter(
        (r) => r.status === 'in_progress' || r.status === 'queued'
      ).length;
      const totalCompleted = blocked + approved;

      setStats({
        totalScans: workflowRuns.length,
        blocked,
        approved,
        blockRate: totalCompleted > 0 ? (blocked / totalCompleted) * 100 : 0,
        inProgress,
      });

      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      console.error('GitHub API Error:', err);
      setError(
        err instanceof Error
          ? `Connection failed: ${err.message}`
          : 'Unknown error connecting to GitHub API'
      );
    } finally {
      setLoading(false);
    }
  }, []);

  // Boot sequence animation
  useEffect(() => {
    const timer = setTimeout(() => setBootSequence(false), 2000);
    return () => clearTimeout(timer);
  }, []);

  // Initial fetch and polling
  useEffect(() => {
    fetchWorkflowRuns();
    const interval = setInterval(fetchWorkflowRuns, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [fetchWorkflowRuns]);

  const getStatusIcon = (conclusion: string | null, status: string) => {
    if (status === 'in_progress' || status === 'queued') {
      return <Loader2 className="h-5 w-5 text-blue-400 animate-spin" />;
    }
    if (conclusion === 'failure') {
      return <XCircle className="h-5 w-5 text-red-500" />;
    }
    if (conclusion === 'success') {
      return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    }
    return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
  };

  const getStatusBadge = (conclusion: string | null, status: string) => {
    if (status === 'in_progress' || status === 'queued') {
      return (
        <span className="px-2 py-1 text-xs font-mono bg-blue-500/20 text-blue-400 border border-blue-500/30 rounded">
          SCANNING
        </span>
      );
    }
    if (conclusion === 'failure') {
      return (
        <span className="px-2 py-1 text-xs font-mono bg-red-500/20 text-red-400 border border-red-500/30 rounded">
          BLOCKED
        </span>
      );
    }
    if (conclusion === 'success') {
      return (
        <span className="px-2 py-1 text-xs font-mono bg-green-500/20 text-green-400 border border-green-500/30 rounded">
          APPROVED
        </span>
      );
    }
    return (
      <span className="px-2 py-1 text-xs font-mono bg-yellow-500/20 text-yellow-400 border border-yellow-500/30 rounded">
        UNKNOWN
      </span>
    );
  };

  // Boot sequence screen
  if (bootSequence) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center font-mono">
        <div className="text-green-500 text-sm space-y-1 animate-pulse">
          <p>[BOOT] Initializing OpsGuard Monitor v1.0.0...</p>
          <p>[BOOT] Loading security modules...</p>
          <p>[BOOT] Establishing secure connection...</p>
          <p>[BOOT] Initializing telemetry feed...</p>
        </div>
        <div className="mt-8">
          <Loader2 className="h-8 w-8 text-green-500 animate-spin" />
        </div>
      </div>
    );
  }

  // Error state
  if (error && !loading) {
    return (
      <div className="min-h-screen bg-gray-950 flex flex-col items-center justify-center font-mono p-4">
        <div className="max-w-md text-center space-y-4">
          <ShieldAlert className="h-16 w-16 text-red-500 mx-auto" />
          <h1 className="text-2xl font-bold text-red-500">CONNECTION FAILED</h1>
          <p className="text-gray-400 text-sm">{error}</p>
          <button
            onClick={fetchWorkflowRuns}
            className="mt-4 px-4 py-2 bg-red-500/20 border border-red-500/50 text-red-400 rounded hover:bg-red-500/30 transition-colors flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="h-4 w-4" />
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 font-sans">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="relative">
              <Shield className="h-8 w-8 text-blue-500" />
              <span className="absolute -top-1 -right-1 h-3 w-3 bg-green-500 rounded-full animate-pulse" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight">
                <span className="text-blue-500">OpsGuard</span>{' '}
                <span className="text-gray-400">Monitor</span>
              </h1>
              <p className="text-xs text-gray-500 font-mono">
                {OWNER}/{REPO}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {lastUpdated && (
              <span className="text-xs text-gray-500 font-mono hidden sm:block">
                Last sync: {formatDistanceToNow(lastUpdated, { addSuffix: true })}
              </span>
            )}
            <button
              onClick={fetchWorkflowRuns}
              disabled={loading}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors disabled:opacity-50"
              title="Refresh data"
            >
              <RefreshCw className={`h-5 w-5 text-gray-400 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        {/* System Status Banner */}
        <div className="bg-gray-900/50 border border-gray-800 rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-green-500" />
            <span className="text-xs font-mono text-green-500">SYSTEM ONLINE</span>
            <span className="text-xs text-gray-600">|</span>
            <span className="text-xs font-mono text-gray-500">
              Pipeline security monitoring active
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="h-4 w-4 text-blue-500 animate-pulse" />
            <span className="text-xs font-mono text-blue-400">LIVE</span>
          </div>
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Total Scans */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 hover:border-gray-700 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <Eye className="h-5 w-5 text-blue-500" />
              <span className="text-xs font-mono text-gray-500">TOTAL</span>
            </div>
            <p className="text-3xl font-bold text-white font-mono">{stats.totalScans}</p>
            <p className="text-sm text-gray-500 mt-1">Pipeline Scans</p>
          </div>

          {/* Block Rate */}
          <div className="bg-gray-900 border border-gray-800 rounded-lg p-5 hover:border-gray-700 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <Zap className="h-5 w-5 text-yellow-500" />
              <span className="text-xs font-mono text-gray-500">RATE</span>
            </div>
            <p className="text-3xl font-bold text-yellow-500 font-mono">
              {stats.blockRate.toFixed(1)}%
            </p>
            <p className="text-sm text-gray-500 mt-1">Block Rate</p>
          </div>

          {/* Blocked Threats */}
          <div className="bg-gray-900 border border-red-900/50 rounded-lg p-5 hover:border-red-800/50 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <ShieldAlert className="h-5 w-5 text-red-500" />
              <span className="text-xs font-mono text-red-500">BLOCKED</span>
            </div>
            <p className="text-3xl font-bold text-red-500 font-mono">{stats.blocked}</p>
            <p className="text-sm text-gray-500 mt-1">Threats Blocked</p>
          </div>

          {/* Approved */}
          <div className="bg-gray-900 border border-green-900/50 rounded-lg p-5 hover:border-green-800/50 transition-colors">
            <div className="flex items-center justify-between mb-3">
              <ShieldCheck className="h-5 w-5 text-green-500" />
              <span className="text-xs font-mono text-green-500">APPROVED</span>
            </div>
            <p className="text-3xl font-bold text-green-500 font-mono">{stats.approved}</p>
            <p className="text-sm text-gray-500 mt-1">Secure Commits</p>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <GitCommit className="h-5 w-5 text-blue-500" />
              <h2 className="font-semibold">Security Scan Feed</h2>
            </div>
            {stats.inProgress > 0 && (
              <span className="text-xs font-mono text-blue-400 flex items-center gap-1">
                <Loader2 className="h-3 w-3 animate-spin" />
                {stats.inProgress} scanning
              </span>
            )}
          </div>

          {loading && runs.length === 0 ? (
            <div className="p-8 text-center">
              <Loader2 className="h-8 w-8 text-blue-500 animate-spin mx-auto mb-3" />
              <p className="text-sm text-gray-500 font-mono">Loading telemetry data...</p>
            </div>
          ) : runs.length === 0 ? (
            <div className="p-8 text-center">
              <Shield className="h-12 w-12 text-gray-700 mx-auto mb-3" />
              <p className="text-gray-500">No workflow runs found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-950/50">
                  <tr className="text-left text-gray-500 font-mono text-xs">
                    <th className="px-5 py-3">STATUS</th>
                    <th className="px-5 py-3">COMMIT</th>
                    <th className="px-5 py-3 hidden md:table-cell">AUTHOR</th>
                    <th className="px-5 py-3 hidden lg:table-cell">BRANCH</th>
                    <th className="px-5 py-3">TIME</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {runs.slice(0, 20).map((run) => (
                    <tr
                      key={run.id}
                      className="hover:bg-gray-800/50 transition-colors cursor-pointer"
                      onClick={() => window.open(run.html_url, '_blank')}
                    >
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(run.conclusion, run.status)}
                          {getStatusBadge(run.conclusion, run.status)}
                        </div>
                      </td>
                      <td className="px-5 py-4">
                        <div className="flex flex-col">
                          <span className="text-gray-200 font-medium truncate max-w-xs">
                            {run.head_commit?.message?.split('\n')[0] || 'No commit message'}
                          </span>
                          <span className="text-xs text-gray-600 font-mono">
                            {run.head_sha.substring(0, 7)}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4 hidden md:table-cell">
                        <div className="flex items-center gap-2">
                          {run.actor?.avatar_url && (
                            <img
                              src={run.actor.avatar_url}
                              alt={run.actor.login}
                              className="h-6 w-6 rounded-full"
                            />
                          )}
                          <span className="text-gray-400">
                            {run.actor?.login || run.head_commit?.author?.name || 'Unknown'}
                          </span>
                        </div>
                      </td>
                      <td className="px-5 py-4 hidden lg:table-cell">
                        <span className="text-xs font-mono text-gray-500 bg-gray-800 px-2 py-1 rounded">
                          {run.head_branch}
                        </span>
                      </td>
                      <td className="px-5 py-4">
                        <span className="text-xs text-gray-500">
                          {formatDistanceToNow(new Date(run.created_at), { addSuffix: true })}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Footer */}
        <footer className="text-center py-4 text-xs text-gray-600 font-mono">
          <p>
            OpsGuard Monitor v1.0.0 | Powered by{' '}
            <span className="text-blue-500">OpsGuard-AI</span>
          </p>
        </footer>
      </main>
    </div>
  );
}
