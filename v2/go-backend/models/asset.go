package models

type Asset struct {
	ID               string                 `json:"id,omitempty"`
	UserID           string                 `json:"user_id,omitempty"`
	OriginalFilename string                 `json:"original_filename"`
	ImagePath        string                 `json:"image_path,omitempty"`
	Source           string                 `json:"source"`
	Labels           []string               `json:"labels,omitempty"`
	Thumbnail        string                 `json:"thumbnail,omitempty"`
	CreatedAt        string                 `json:"created_at"`
	Metadata         map[string]interface{} `json:"metadata,omitempty"`
}

type UpdateAsset struct {
	Labels    []string               `json:"labels,omitempty"`
	Thumbnail string                 `json:"thumbnail,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}
