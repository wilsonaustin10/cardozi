import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface Project {
  id: string;
  status: string;
  system_prompt?: string;
  output_schema?: Record<string, any>;
  auth_cookies?: Record<string, any>;
  live_stream_url?: string;
  active_session_id?: string;
}

export interface CreateProjectRequest {
  system_prompt: string;
  output_schema?: Record<string, any>;
}

// API methods
export const apiClient = {
  // Health check
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  // Projects
  async createProject(data: CreateProjectRequest): Promise<Project> {
    const response = await api.post('/projects/', data);
    return response.data;
  },

  async getProjects(): Promise<Project[]> {
    const response = await api.get('/projects/');
    return response.data;
  },

  async getProject(id: string): Promise<Project> {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },

  async startProject(id: string) {
    const response = await api.post(`/projects/${id}/start`);
    return response.data;
  },

  async stopProject(id: string) {
    const response = await api.post(`/projects/${id}/stop`);
    return response.data;
  },

  async deleteProject(id: string) {
    const response = await api.delete(`/projects/${id}`);
    return response.data;
  },
};

export default api;