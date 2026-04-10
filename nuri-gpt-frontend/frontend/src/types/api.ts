export interface Template {
  id: string;
  name: string;
  template_type: string;
  structure_json: Record<string, unknown>;
  semantic_json?: Record<string, unknown>;
  is_default: boolean;
  user_id: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  last_used_at?: string;
}

export interface OcrResponse {
  storage_info?: Record<string, unknown>;
  extracted_text: string;
  normalized_text: string;
}

export interface GenerateLogRequest {
  semantic_json?: Record<string, unknown>;
  ocr_text?: string;
  template_id?: string;
  additional_guidelines?: string;
  child_age: number;  // 필수: 0-5 범위
  is_aggressive?: string; // "true" or "false"
}

export interface GenerateLogResponse {
  updated_activities?: Record<string, unknown>[];
  template_mapping?: Record<string, unknown>;
  semantic_json?: Record<string, unknown>;
  status: string;
  message: string;
  observation_content?: string;
  evaluation_content?: string;
  development_areas?: string[];
}

export interface ActivityComment {
  target_id: string;
  comment: string;
}

export interface RegenerateLogRequest {
  original_semantic_json: Record<string, unknown>;
  current_activities: Record<string, unknown>[];
  comments: ActivityComment[];
  additional_guidelines?: string;
  child_age?: number;
  is_aggressive?: string;
}

export interface RegenerateLogResponse {
  updated_activities: Record<string, unknown>[];
  log_id: string;
}

export interface JournalResponse {
  id: string;
  user_id: string;
  group_id: string;
  version: number;
  is_final: boolean;
  title?: string;
  observation_content?: string;
  evaluation_content?: string;
  development_areas?: string[];
  template_id?: string;
  template_mapping?: Record<string, unknown>;
  semantic_json?: Record<string, unknown>;
  updated_activities?: Record<string, unknown>[];
  source_type?: string;
  ocr_text?: string;
  additional_guidelines?: string;
  created_at: string;
  updated_at: string;
}

export interface JournalListResponse {
  items: JournalResponse[];
  total: number;
  limit: number;
  offset: number;
}
