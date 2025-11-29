'use client';

import { useEffect, useState } from 'react';
import { Project, apiClient } from '@/lib/api';
import { ProjectCard } from '@/components/ProjectCard';
import { CreateProjectForm } from '@/components/CreateProjectForm';
import { RefreshCw, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadProjects = async () => {
    try {
      setError(null);
      const data = await apiClient.getProjects();
      setProjects(data);
    } catch (err) {
      console.error('Failed to load projects:', err);
      setError('Failed to load projects. Please check your API connection.');
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadProjects();
  };

  const handleProjectCreated = () => {
    loadProjects();
  };

  const handleDeleteProject = async (project: Project) => {
    if (confirm(`Are you sure you want to delete project ${project.id.slice(0, 8)}...?`)) {
      try {
        await apiClient.deleteProject(project.id);
        loadProjects(); // Refresh the list
      } catch (error) {
        console.error('Failed to delete project:', error);
        alert('Failed to delete project. Please try again.');
      }
    }
  };

  const handleViewProject = (project: Project) => {
    // TODO: Navigate to project detail view
    console.log('View project:', project);
  };

  const handleStartProject = async (project: Project) => {
    try {
      await apiClient.startProject(project.id);
      loadProjects(); // Refresh to see updated status
    } catch (error) {
      console.error('Failed to start project:', error);
      alert('Failed to start project. Please try again.');
    }
  };

  const handleStopProject = async (project: Project) => {
    try {
      await apiClient.stopProject(project.id);
      loadProjects(); // Refresh to see updated status
    } catch (error) {
      console.error('Failed to stop project:', error);
      alert('Failed to stop project. Please try again.');
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Cardozi CRM Agent</h1>
              <p className="text-gray-600 mt-2">Manage your automated CRM projects</p>
            </div>
            <Button 
              variant="outline" 
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-2 text-red-700">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Create Project Form */}
          <div className="lg:col-span-1">
            <CreateProjectForm onProjectCreated={handleProjectCreated} />
          </div>

          {/* Projects Grid */}
          <div className="lg:col-span-2">
            {isLoading ? (
              <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <span className="ml-3 text-gray-600">Loading projects...</span>
              </div>
            ) : projects.length === 0 ? (
              <div className="text-center py-12">
                <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
                <p className="text-gray-500">Create your first CRM agent project to get started.</p>
              </div>
            ) : (
              <div className="grid gap-4">
                {projects.map((project) => (
                  <ProjectCard
                    key={project.id}
                    project={project}
                    onView={handleViewProject}
                    onStart={handleStartProject}
                    onStop={handleStopProject}
                    onDelete={handleDeleteProject}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}