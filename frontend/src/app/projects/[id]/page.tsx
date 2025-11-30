'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { PlayCircle, PauseCircle, RotateCw, ExternalLink, Loader2 } from 'lucide-react'

interface Project {
  id: string
  name: string
  description: string
  status: 'INITIALIZING' | 'IDLE' | 'RUNNING' | 'BLOCKED'
  system_prompt: string
  output_schema: any
  auth_cookies: any
  live_stream_url: string | null
  active_session_id: string | null
  created_at: string
  updated_at: string
}

export default function ProjectDetailPage() {
  const params = useParams()
  const router = useRouter()
  const projectId = params.id as string
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [executing, setExecuting] = useState(false)

  useEffect(() => {
    fetchProject()
    // Poll for updates while running
    const interval = setInterval(() => {
      if (project?.status === 'RUNNING' || project?.status === 'BLOCKED') {
        fetchProject()
      }
    }, 2000)
    return () => clearInterval(interval)
  }, [projectId, project?.status])

  const fetchProject = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}`)
      if (!res.ok) throw new Error('Failed to fetch project')
      const data = await res.json()
      setProject(data)
    } catch (error) {
      console.error('Error fetching project:', error)
    } finally {
      setLoading(false)
    }
  }

  const runAgent = async () => {
    setExecuting(true)
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/projects/${projectId}/run`, {
        method: 'POST',
      })
      if (!res.ok) throw new Error('Failed to start agent')
      await fetchProject()
    } catch (error) {
      console.error('Error running agent:', error)
    } finally {
      setExecuting(false)
    }
  }

  const resumeAgent = async () => {
    // Resume a blocked session by re-opening the intervention URL
    if (project?.live_stream_url) {
      window.open(project.live_stream_url, '_blank')
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'INITIALIZING': return 'bg-gray-500'
      case 'IDLE': return 'bg-green-500'
      case 'RUNNING': return 'bg-blue-500'
      case 'BLOCKED': return 'bg-orange-500'
      default: return 'bg-gray-500'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p>Project not found</p>
      </div>
    )
  }

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="mb-6">
        <Button variant="outline" onClick={() => router.push('/')}>
          ← Back to Projects
        </Button>
      </div>

      <div className="grid gap-6">
        {/* Project Overview */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle>{project.name}</CardTitle>
                <CardDescription>{project.description}</CardDescription>
              </div>
              <Badge className={getStatusColor(project.status)}>
                {project.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div>
                <h3 className="font-semibold mb-2">System Prompt</h3>
                <p className="text-sm text-gray-600 whitespace-pre-wrap">
                  {project.system_prompt || 'No system prompt configured'}
                </p>
              </div>
              
              <div>
                <h3 className="font-semibold mb-2">Output Schema</h3>
                <pre className="text-sm bg-gray-100 p-3 rounded overflow-x-auto">
                  {JSON.stringify(project.output_schema, null, 2) || '{}'}
                </pre>
              </div>

              <div className="flex gap-4">
                {project.status === 'IDLE' && (
                  <Button onClick={runAgent} disabled={executing}>
                    {executing ? (
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <PlayCircle className="mr-2 h-4 w-4" />
                    )}
                    Run Agent
                  </Button>
                )}
                
                {project.status === 'RUNNING' && (
                  <Button variant="outline" disabled>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Agent Running...
                  </Button>
                )}
                
                {project.status === 'BLOCKED' && (
                  <Button onClick={resumeAgent} variant="destructive">
                    <ExternalLink className="mr-2 h-4 w-4" />
                    Manual Intervention Required
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Live Browser Stream */}
        {project.live_stream_url && (project.status === 'RUNNING' || project.status === 'BLOCKED') && (
          <Card>
            <CardHeader>
              <CardTitle>Live Browser Session</CardTitle>
              <CardDescription>
                {project.status === 'BLOCKED' 
                  ? 'Agent needs help - click the intervention button above to take control'
                  : 'Watch the agent work in real-time'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="relative bg-gray-900 rounded-lg overflow-hidden" style={{ height: '600px' }}>
                <iframe
                  src={project.live_stream_url}
                  className="w-full h-full"
                  title="Browser Stream"
                  allow="fullscreen"
                />
              </div>
            </CardContent>
          </Card>
        )}

        {/* Session Info */}
        {project.active_session_id && (
          <Card>
            <CardHeader>
              <CardTitle>Session Information</CardTitle>
            </CardHeader>
            <CardContent>
              <dl className="grid grid-cols-1 gap-2 text-sm">
                <div>
                  <dt className="font-semibold">Session ID:</dt>
                  <dd className="font-mono">{project.active_session_id}</dd>
                </div>
                {project.auth_cookies && (
                  <div>
                    <dt className="font-semibold">Cookies:</dt>
                    <dd>{Object.keys(project.auth_cookies).length} cookie(s) stored</dd>
                  </div>
                )}
                <div>
                  <dt className="font-semibold">Created:</dt>
                  <dd>{new Date(project.created_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt className="font-semibold">Updated:</dt>
                  <dd>{new Date(project.updated_at).toLocaleString()}</dd>
                </div>
              </dl>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}