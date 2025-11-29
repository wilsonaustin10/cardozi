'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { apiClient, CreateProjectRequest } from '@/lib/api';
import { Plus, Loader2 } from 'lucide-react';

interface CreateProjectFormProps {
  onProjectCreated?: () => void;
}

export function CreateProjectForm({ onProjectCreated }: CreateProjectFormProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    system_prompt: '',
    output_schema: '{}',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const data: CreateProjectRequest = {
        system_prompt: formData.system_prompt,
        output_schema: formData.output_schema ? JSON.parse(formData.output_schema) : undefined,
      };

      await apiClient.createProject(data);
      
      // Reset form and close
      setFormData({ system_prompt: '', output_schema: '{}' });
      setIsOpen(false);
      onProjectCreated?.();
    } catch (error) {
      console.error('Failed to create project:', error);
      alert('Failed to create project. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) {
    return (
      <Button onClick={() => setIsOpen(true)} className="w-full">
        <Plus className="w-4 h-4 mr-2" />
        Create New Project
      </Button>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-gray-900">Create New Project</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="system_prompt" className="block text-sm font-medium mb-2 text-gray-700">
              System Prompt *
            </label>
            <textarea
              id="system_prompt"
              value={formData.system_prompt}
              onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
              placeholder="Enter the system prompt for your CRM agent..."
              className="w-full p-3 border border-gray-300 rounded-md resize-none h-24 text-gray-900 placeholder-gray-500 bg-white"
              required
            />
          </div>

          <div>
            <label htmlFor="output_schema" className="block text-sm font-medium mb-2 text-gray-700">
              Output Schema (JSON)
            </label>
            <textarea
              id="output_schema"
              value={formData.output_schema}
              onChange={(e) => setFormData({ ...formData, output_schema: e.target.value })}
              placeholder='{"customer_name": "string", "contact_info": "object"}'
              className="w-full p-3 border border-gray-300 rounded-md resize-none h-20 font-mono text-sm text-gray-900 placeholder-gray-500 bg-white"
            />
          </div>

          <div className="flex gap-2">
            <Button type="submit" disabled={isLoading || !formData.system_prompt}>
              {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              Create Project
            </Button>
            <Button type="button" variant="outline" onClick={() => setIsOpen(false)}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}