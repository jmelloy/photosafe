package models

type Asset struct {
	ID        string                 `json:"id,omitempty"`
	ImagePath string                 `json:"image_path"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}
