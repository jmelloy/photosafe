package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/fs"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"go-backend/models"
)

type Asset models.Asset

func main() {
	// Initialize Elasticsearch client
	var err error

	// Folder to scan
	folderPath := "./images"
	if len(os.Args) > 1 {
		folderPath = os.Args[1]
	}

	log.Printf("Scanning folder: %s", folderPath)
	err = processFolder(folderPath)
	if err != nil {
		log.Fatalf("Error processing folder: %s", err)
	}

	log.Println("Processing completed!")
}

func processFolder(folderPath string) error {
	// Walk through the folder
	return filepath.WalkDir(folderPath, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return fmt.Errorf("error accessing file %s: %w", path, err)
		}

		// Skip directories
		if d.IsDir() {
			return nil
		}

		// Check if the file is an image
		if isImageFile(path) {
			// Process the image
			log.Printf("Processing image: %s", path)

			// Attempt to read metadata from meta.json
			metaData, err := readMetaJSON(filepath.Dir(path))
			if err != nil {
				log.Printf("Error reading metadata for %s: %s", path, err)
			}

			// Add to Elasticsearch via API
			err = addImageToAPI(path, metaData)
			if err != nil {
				log.Printf("Error adding image to API: %s", err)
			}
		}

		return nil
	})
}

func isImageFile(path string) bool {
	extensions := []string{".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
	ext := strings.ToLower(filepath.Ext(path))
	for _, validExt := range extensions {
		if ext == validExt {
			return true
		}
	}
	return false
}

func readMetaJSON(folderPath string) (map[string]interface{}, error) {
	metaFilePath := filepath.Join(folderPath, "meta.json")

	// Check if meta.json exists
	if _, err := os.Stat(metaFilePath); os.IsNotExist(err) {
		return nil, nil // No metadata file, return empty map
	}

	// Read and parse meta.json
	metaData := make(map[string]interface{})
	fileBytes, err := os.ReadFile(metaFilePath)
	if err != nil {
		return nil, fmt.Errorf("error reading meta.json: %w", err)
	}

	err = json.Unmarshal(fileBytes, &metaData)
	if err != nil {
		return nil, fmt.Errorf("error parsing meta.json: %w", err)
	}

	return metaData, nil
}

func addImageToAPI(imagePath string, metadata map[string]interface{}) error {
	// Create a document with the image path and metadata
	var doc Asset

	if id, ok := metadata["id"].(string); ok {
		doc = Asset{
			ID:        id,
			ImagePath: imagePath,
			Metadata:  metadata,
		}

	} else {
		doc = Asset{
			ImagePath: imagePath,
			Metadata:  metadata,
		}
	}

	// Serialize the document to JSON
	docBytes, err := json.Marshal(doc)
	if err != nil {
		return fmt.Errorf("error serializing document: %w", err)
	}

	// Call the main Go API to handle the image indexing
	apiURL := "http://localhost:8080/assets"
	req, err := http.NewRequest("POST", apiURL, bytes.NewBuffer(docBytes))
	if err != nil {
		return fmt.Errorf("error creating request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	// Send the POST request to the API
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("error sending request to API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode > 399 {
		return fmt.Errorf("received non-OK response from API: %s", resp.Status)
	}

	return nil
}
