package routes

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"go-backend/middleware"
	"go-backend/models"

	"github.com/gorilla/mux"
)

const assetDirectory = "./assets"

func CreateAsset(w http.ResponseWriter, r *http.Request) {
	esClient := middleware.GetElasticsearchClient(r)

	user, err := AuthenticateUserFromToken(r, esClient)
	if err != nil {
		http.Error(w, "Failed to authenticate user", http.StatusUnauthorized)
		return
	}

	if err := r.ParseMultipartForm(10 << 20); err != nil { // 10 MB max memory
		http.Error(w, fmt.Sprintf("Error parsing form: %s", err), http.StatusBadRequest)
		return
	}

	// Get the file from the form
	file, handler, err := r.FormFile("file")
	if err != nil {
		http.Error(w, fmt.Sprintf("Error retrieving the file: %s", err), http.StatusBadRequest)
		return
	}
	defer file.Close()

	date := time.Now()

	asset := models.Asset{
		ID:               r.FormValue("id"),
		UserID:           user.ID,
		OriginalFilename: handler.Filename,
		CreatedAt:        r.FormValue("created_at"),
	}

	docBytes, _ := json.Marshal(asset)

	res, err := esClient.Index(
		"assets-"+user.ID, // Index name
		bytes.NewReader(docBytes),
		esClient.Index.WithDocumentID(asset.ID),
	)

	filename := r.URL.Query().Get("filename")
	if filename == "" {
		http.Error(w, "Filename is required", http.StatusBadRequest)
		return
	}

	docPath := filepath.Join(assetDirectory, user.ID, date.Format("2006/01/02"), asset.ID)
	if err := os.MkdirAll(docPath, os.ModePerm); err != nil {
		log.Fatalf("Error creating asset directory: %s", err)
	}
	filepath := filepath.Join(docPath, filename)
	asset.ImagePath = filepath

	assetBytes, _ := json.Marshal(asset)
	esClient.Index("assets-"+user.ID, bytes.NewReader(assetBytes), esClient.Index.WithDocumentID(asset.ID))

	if err != nil {
		log.Print(err)

		http.Error(w, "Failed to create document", http.StatusInternalServerError)
		return
	}

	defer res.Body.Close()

	if res.IsError() {
		log.Print(res)
		http.Error(w, "Failed to create document", http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"message": "Document created successfully"}`))
}

func GetAsset(w http.ResponseWriter, r *http.Request) {
	esClient := middleware.GetElasticsearchClient(r)
	user, err := AuthenticateUserFromToken(r, esClient)
	if err != nil {
		http.Error(w, "Failed to authenticate user", http.StatusUnauthorized)
		return
	}

	vars := mux.Vars(r)
	id := vars["id"]

	res, err := esClient.Get("assets-"+user.ID, id)
	if err != nil {
		http.Error(w, "Failed to fetch document", http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	if res.IsError() {
		http.Error(w, "Document not found", http.StatusNotFound)
		return
	}

	var doc map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&doc); err != nil {
		http.Error(w, "Error parsing response", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(doc)
}

func UpdateAsset(w http.ResponseWriter, r *http.Request) {
	esClient := middleware.GetElasticsearchClient(r)
	user, err := AuthenticateUserFromToken(r, esClient)
	if err != nil {
		http.Error(w, "Failed to authenticate user", http.StatusUnauthorized)
		return
	}

	vars := mux.Vars(r)
	id := vars["id"]

	var doc models.UpdateAsset
	if err := json.NewDecoder(r.Body).Decode(&doc); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	// Serialize the document to JSON for updating
	docBytes, _ := json.Marshal(doc)

	res, err := esClient.Update("assets-"+user.ID, id, bytes.NewReader([]byte(`{"doc": `+string(docBytes)+`}`)))
	if err != nil {
		http.Error(w, "Failed to update document", http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message": "Document updated successfully"}`))
}

func DeleteAsset(w http.ResponseWriter, r *http.Request) {
	esClient := middleware.GetElasticsearchClient(r)

	vars := mux.Vars(r)
	id := vars["id"]

	res, err := esClient.Delete("documents", id)
	if err != nil {
		http.Error(w, "Failed to delete document", http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	if res.IsError() {
		http.Error(w, "Document not found", http.StatusNotFound)
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message": "Document deleted successfully"}`))
}

func ListAssets(w http.ResponseWriter, r *http.Request) {
	esClient := middleware.GetElasticsearchClient(r)

	res, err := esClient.Search(
		esClient.Search.WithIndex("documents"),
		esClient.Search.WithSize(100), // Limit the number of results (adjust as needed)
	)
	if err != nil {
		http.Error(w, "Failed to fetch documents", http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	if res.IsError() {
		http.Error(w, "Error retrieving documents", http.StatusInternalServerError)
		return
	}

	var result map[string]interface{}
	if err := json.NewDecoder(res.Body).Decode(&result); err != nil {
		http.Error(w, "Error parsing response", http.StatusInternalServerError)
		return
	}

	// Extract and format the documents
	hits := result["hits"].(map[string]interface{})["hits"].([]interface{})
	var documents []models.Asset
	for _, hit := range hits {
		doc := hit.(map[string]interface{})["_source"]
		jsonDoc, _ := json.Marshal(doc)
		var document models.Asset
		json.Unmarshal(jsonDoc, &document)
		documents = append(documents, document)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(documents)
}
