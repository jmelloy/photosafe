/**
 * Type definitions for PhotoSafe API
 * Based on backend/app/schemas.py
 */

export interface Version {
  id: number;
  photo_uuid?: string;
  version: string;
  s3_path: string;
  filename?: string;
  width?: number;
  height?: number;
  size?: number;
  type?: string;
}

export interface Photo {
  uuid: string;
  masterFingerprint?: string;
  original_filename: string;
  date: string;
  description?: string;
  title?: string;
  keywords?: string[];
  labels?: string[];
  albums?: string[];
  persons?: string[];
  faces?: Record<string, any>;
  favorite?: boolean;
  hidden?: boolean;
  isphoto?: boolean;
  ismovie?: boolean;
  burst?: boolean;
  live_photo?: boolean;
  portrait?: boolean;
  screenshot?: boolean;
  slow_mo?: boolean;
  time_lapse?: boolean;
  hdr?: boolean;
  selfie?: boolean;
  panorama?: boolean;
  intrash?: boolean;
  latitude?: number;
  longitude?: number;
  uti?: string;
  date_modified?: string;
  place?: Record<string, any>;
  exif?: Record<string, any>;
  score?: Record<string, any>;
  search_info?: Record<string, any>;
  fields?: Record<string, any>;
  height?: number;
  width?: number;
  size?: number;
  orientation?: number;
  s3_key_path?: string;
  s3_thumbnail_path?: string;
  s3_edited_path?: string;
  s3_original_path?: string;
  s3_live_path?: string;
  library?: string;
  uploaded_at?: string;
  versions?: Version[];
  // Backwards compatibility fields
  filename?: string;
  file_path?: string;
  content_type?: string;
  file_size?: number;
  // Computed fields for frontend
  id?: string; // Alias for uuid
  url?: string; // Computed URL for display
}

export interface Album {
  uuid: string;
  title: string;
  creation_date?: string;
  start_date?: string;
  end_date?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  name?: string;
  is_active: boolean;
  is_superuser: boolean;
  date_joined: string;
  last_login?: string;
}

export interface Library {
  id: number;
  name: string;
  path?: string;
  description?: string;
  owner_id: number;
  created_at: string;
  updated_at: string;
}

export interface PhotoCreateData {
  uuid: string;
  masterFingerprint?: string;
  original_filename: string;
  date: string;
  description?: string;
  title?: string;
  keywords?: string[];
  labels?: string[];
  albums?: string[];
  persons?: string[];
  versions?: Omit<Version, 'id' | 'photo_uuid'>[];
}

export interface PhotoUpdateData {
  masterFingerprint?: string;
  original_filename?: string;
  date?: string;
  description?: string;
  title?: string;
  keywords?: string[];
  labels?: string[];
  albums?: string[];
  persons?: string[];
  faces?: Record<string, any>;
  favorite?: boolean;
  hidden?: boolean;
  [key: string]: any;
}
