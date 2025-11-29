import { Project } from '@/lib/api';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Eye, Play, Pause, Trash2 } from 'lucide-react';

interface ProjectCardProps {
  project: Project;
  onView?: (project: Project) => void;
  onStart?: (project: Project) => void;
  onStop?: (project: Project) => void;
  onDelete?: (project: Project) => void;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'RUNNING': return 'bg-green-100 text-green-800 border-green-200';
    case 'IDLE': return 'bg-blue-100 text-blue-800 border-blue-200';
    case 'BLOCKED': return 'bg-red-100 text-red-800 border-red-200';
    case 'INITIALIZING': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    default: return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

export function ProjectCard({ 
  project, 
  onView, 
  onStart, 
  onStop, 
  onDelete 
}: ProjectCardProps) {
  
  const handleViewClick = () => {
    console.log('View button clicked for project:', project.id);
    onView?.(project);
  };
  
  const handleStartClick = () => {
    console.log('Start button clicked for project:', project.id);
    onStart?.(project);
  };
  
  const handleStopClick = () => {
    console.log('Stop button clicked for project:', project.id);
    onStop?.(project);
  };
  
  const handleDeleteClick = () => {
    console.log('Delete button clicked for project:', project.id);
    onDelete?.(project);
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg truncate text-gray-900">{project.id.slice(0, 8)}...</CardTitle>
          <span 
            className={`px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(project.status)}`}
          >
            {project.status}
          </span>
        </div>
        <CardDescription className="line-clamp-2 text-gray-600">
          {project.system_prompt || 'No system prompt configured'}
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-2 text-sm text-gray-600">
          {project.live_stream_url && (
            <div>
              <span className="font-medium">Stream URL:</span>
              <span className="ml-2 truncate block">{project.live_stream_url}</span>
            </div>
          )}
          {project.active_session_id && (
            <div>
              <span className="font-medium">Session ID:</span>
              <span className="ml-2">{project.active_session_id.slice(0, 8)}...</span>
            </div>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="flex gap-2">
        <Button variant="outline" size="sm" onClick={handleViewClick}>
          <Eye className="w-4 h-4 mr-1" />
          View
        </Button>
        
        {(project.status === 'IDLE' || project.status === 'INITIALIZING') && (
          <Button variant="default" size="sm" onClick={handleStartClick}>
            <Play className="w-4 h-4 mr-1" />
            Start
          </Button>
        )}
        
        {project.status === 'RUNNING' && (
          <Button variant="secondary" size="sm" onClick={handleStopClick}>
            <Pause className="w-4 h-4 mr-1" />
            Stop
          </Button>
        )}
        
        <Button variant="destructive" size="sm" onClick={handleDeleteClick}>
          <Trash2 className="w-4 h-4 mr-1" />
          Delete
        </Button>
      </CardFooter>
    </Card>
  );
}