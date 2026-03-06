/**
 * api.ts
 * -------
 * Typed fetch client for the FastAPI backend.
 * All functions map to real routes registered in backend/main.py.
 *
 * Set NEXT_PUBLIC_API_URL in studio-ui/.env.local to override the default.
 */

const API_URL =
  (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

// ── Error class ───────────────────────────────────────────────────────────────

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

// ── Generic helper ────────────────────────────────────────────────────────────

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const json = await res.json();
      detail = json?.detail ?? detail;
    } catch {
      // ignore JSON parse errors
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface Project {
  project_id: string;
  title: string;
  description?: string;
  created_at: string;
}

export interface UploadResponse {
  document_id: string;
  project_id: string;
  text_length: number;
  file_path: string;
}

export interface Script {
  script_id: string;
  project_id: string;
  title: string;
  content: string;
  created_at: string;
}

export interface Scene {
  scene_id: string;
  scene_title: string;
  project_id: string;
  subscenes: unknown[];
}

export interface RenderResponse {
  video_url: string;
  scene_count: number;
  chunk_count: number;
}

// ── Projects ──────────────────────────────────────────────────────────────────

/** POST /api/v1/projects/ */
export async function createProject(
  title: string,
  description?: string,
): Promise<Project> {
  return request<Project>("/api/v1/projects/", {
    method: "POST",
    body: JSON.stringify({ title, description }),
  });
}

/** GET /api/v1/projects/ */
export async function listProjects(skip = 0, limit = 20): Promise<Project[]> {
  return request<Project[]>(`/api/v1/projects/?skip=${skip}&limit=${limit}`);
}

/** GET /api/v1/projects/{project_id} */
export async function getProject(projectId: string): Promise<Project> {
  return request<Project>(`/api/v1/projects/${projectId}`);
}

/** DELETE /api/v1/projects/{project_id} */
export async function deleteProject(projectId: string): Promise<void> {
  return request<void>(`/api/v1/projects/${projectId}`, { method: "DELETE" });
}

// ── Upload ────────────────────────────────────────────────────────────────────

/**
 * POST /api/v1/upload/
 * Multipart — do NOT set Content-Type manually; the browser sets it with boundary.
 */
export async function uploadFile(
  file: File,
  title: string,
  description?: string,
): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  if (description) form.append("description", description);

  const res = await fetch(`${API_URL}/api/v1/upload/`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const json = await res.json();
      detail = json?.detail ?? detail;
    } catch {
      // ignore
    }
    throw new ApiError(res.status, detail);
  }

  return res.json() as Promise<UploadResponse>;
}

// ── Scripts ───────────────────────────────────────────────────────────────────

/** POST /api/v1/scripts/ */
export async function createScript(
  projectId: string,
  title: string,
  content: string,
): Promise<Script> {
  return request<Script>("/api/v1/scripts/", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, title, content }),
  });
}

/** GET /api/v1/scripts/ */
export async function listScripts(projectId?: string, skip = 0, limit = 20): Promise<Script[]> {
  const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
  if (projectId) params.set("project_id", projectId);
  return request<Script[]>(`/api/v1/scripts/?${params}`);
}

/** GET /api/v1/scripts/{script_id} */
export async function getScript(scriptId: string): Promise<Script> {
  return request<Script>(`/api/v1/scripts/${scriptId}`);
}

/** PUT /api/v1/scripts/{script_id} */
export async function updateScript(
  scriptId: string,
  projectId: string,
  title: string,
  content: string,
): Promise<Script> {
  return request<Script>(`/api/v1/scripts/${scriptId}`, {
    method: "PUT",
    body: JSON.stringify({ project_id: projectId, title, content }),
  });
}

/** DELETE /api/v1/scripts/{script_id} */
export async function deleteScript(scriptId: string): Promise<void> {
  return request<void>(`/api/v1/scripts/${scriptId}`, { method: "DELETE" });
}

// ── Scenes ────────────────────────────────────────────────────────────────────

/** POST /api/v1/scenes/create — generates a new scene for a project */
export async function generateScenes(
  projectId: string,
  sceneTitle: string,
): Promise<Scene> {
  return request<Scene>("/api/v1/scenes/create", {
    method: "POST",
    body: JSON.stringify({ project_id: projectId, scene_title: sceneTitle }),
  });
}

// ── Script generation (alias for clarity) ────────────────────────────────────

/**
 * generateScript — creates a script record in the backend.
 * The LLM content should be passed in as `content`.
 */
export async function generateScript(
  projectId: string,
  title: string,
  content: string,
): Promise<Script> {
  return createScript(projectId, title, content);
}

// ── Render Pipeline ───────────────────────────────────────────────────────────

/**
 * POST /api/v1/render/
 * Triggers the full pipeline: script → scene generation → Manim → FFmpeg → MP4.
 */
export async function renderVideo(scriptId: string): Promise<RenderResponse> {
  return request<RenderResponse>("/api/v1/render/", {
    method: "POST",
    body: JSON.stringify({ script_id: scriptId }),
  });
}
