package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"mime/multipart"
	"net/http"
	"os"
	"path/filepath"
	"strings"

	"go-backend/models"
)

type Asset models.Asset

func main() {
	token := flag.String("token", "", "The token for the user")
	path := flag.String("path", "", "The path to the images directory")
	apiEndpoint := flag.String("url", "http://localhost:8080/assets", "The API URL for asset creation")
	source := flag.String("source", "", "The source of the images")

	flag.Parse()

	if *token == "" {
		fmt.Println("Error: token is required.")
		flag.Usage()
		os.Exit(1)
	}

	if *path == "" {
		fmt.Println("Error: path is required.")
		flag.Usage()
		os.Exit(1)
	}

	if *source == "" {
		source = path
	}

	folderPath := *path

	log.Printf("Scanning folder: %s", folderPath)

	// Walk through the directory and process each file
	err := filepath.Walk(folderPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return fmt.Errorf("error accessing path %q: %v", path, err)
		}

		// Skip directories
		if info.IsDir() {
			return nil
		}

		// Check if the file is an image based on its extension
		if !isImageFile(path) {
			fmt.Printf("Skipping non-image file: %s\n", path)
			return nil
		}
		// Attempt to read metadata from meta.json
		metaData, err := readMetaJSON(filepath.Dir(path))
		if err != nil {
			log.Printf("Error reading metadata for %s: %s", path, err)
		}

		assetFields := map[string]string{
			"id":     metaData["id"].(string),
			"source": *source,
		}

		// Upload the image
		fmt.Printf("Uploading file: %s\n", path)
		if err := uploadFile(*apiEndpoint, path, assetFields, *token); err != nil {
			fmt.Printf("Failed to upload file %s: %v\n", path, err)
		}
		return nil
	})

	if err != nil {
		log.Fatalf("Error processing folder: %s", err)
	}

	log.Println("Processing completed!")
}

func isImageFile(path string) bool {
	extensions := []string{".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".heic"}
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

// uploadFile uploads a file to the specified API endpoint
func uploadFile(url string, filePath string, assetFields map[string]string, token string) error {
	// Open the file
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("failed to open file %s: %v", filePath, err)
	}
	defer file.Close()

	// Create a buffer to hold the multipart data
	body := &bytes.Buffer{}
	writer := multipart.NewWriter(body)

	// Add the file to the multipart form
	part, err := writer.CreateFormFile("file", filepath.Base(filePath))
	if err != nil {
		return fmt.Errorf("failed to create form file: %v", err)
	}

	// Copy the file's content into the multipart writer
	if _, err := io.Copy(part, file); err != nil {
		return fmt.Errorf("failed to write file to form: %v", err)
	}

	// Add additional fields to the form
	for key, value := range assetFields {
		if err := writer.WriteField(key, value); err != nil {
			return fmt.Errorf("failed to write field %s: %v", key, err)
		}
	}

	// Close the writer to finalize the multipart data
	if err := writer.Close(); err != nil {
		return fmt.Errorf("failed to close writer: %v", err)
	}

	// Make the POST request
	req, err := http.NewRequest("POST", url, body)
	if err != nil {
		return fmt.Errorf("failed to create request: %v", err)
	}
	req.Header.Set("Content-Type", writer.FormDataContentType())
	req.Header.Set("Authorization", "Bearer "+token)

	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to send request: %v", err)
	}
	defer resp.Body.Close()

	// Check the response status
	if resp.StatusCode != http.StatusOK {
		respBody, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("server returned non-OK status: %s, body: %s", resp.Status, string(respBody))
	}

	fmt.Printf("Successfully uploaded file: %s\n", filePath)
	return nil
}
