package main

import (
	"bytes"
	"crypto/tls"
	"encoding/json"
	"log"
	"net/http"
	"time"

	"github.com/elastic/go-elasticsearch/v8"
	"github.com/gorilla/mux"

	"go-backend/models"
)

type Document models.Document

var esClient *elasticsearch.Client

// Add CORS headers in the Go API handler
func enableCors(w *http.ResponseWriter) {
	(*w).Header().Set("Access-Control-Allow-Origin", "*")
	(*w).Header().Set("Access-Control-Allow-Methods", "GET, OPTIONS")
	(*w).Header().Set("Access-Control-Allow-Headers", "Content-Type")
}

// LoggingMiddleware is a custom middleware that logs when a request finishes
func LoggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Record the start time of the request
		start := time.Now()

		// Call the next handler in the chain
		next.ServeHTTP(w, r)

		// Log request finished with duration
		duration := time.Since(start)
		log.Printf("%s %s (%v)", r.Method, r.URL.Path, duration)
	})
}

func main() {
	var err error

	transport := &http.Transport{
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true, // Disable TLS certificate verification
		},
	}

	cfg := elasticsearch.Config{
		Addresses: []string{
			"https://es01:9200", // Set the Elasticsearch address here
			"https://es02:9200", // Set the Elasticsearch address here
			"https://es03:9200", // Set the Elasticsearch address here
		},
		Transport: transport,
		Username:  "elastic",
		Password:  "changeit",
	}

	// Create a new Elasticsearch client
	esClient, err = elasticsearch.NewClient(cfg)

	if err != nil {
		log.Fatalf("Error creating Elasticsearch client: %s", err)
	}

	router := mux.NewRouter()

	loggedRouter := LoggingMiddleware(router)

	router.HandleFunc("/assets", createAsset).Methods("POST")
	router.HandleFunc("/assets/{id}", getAsset).Methods("GET")
	router.HandleFunc("/assets/{id}", updateAsset).Methods("PUT")
	router.HandleFunc("/assets/{id}", deleteAsset).Methods("DELETE")
	router.HandleFunc("/assets", listAssets).Methods("GET")

	log.Println("Server running on port 8080")
	log.Fatal(http.ListenAndServe(":8080", loggedRouter))
}

func createAsset(w http.ResponseWriter, r *http.Request) {
	var doc Document
	if err := json.NewDecoder(r.Body).Decode(&doc); err != nil {
		log.Print(err)
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	// Serialize the document to JSON for indexing
	docBytes, _ := json.Marshal(doc)

	res, err := esClient.Index(
		"assets", // Index name
		bytes.NewReader(docBytes),
		esClient.Index.WithDocumentID(doc.ID),
	)

	if err != nil || res.IsError() {
		log.Print(err)
		log.Print(res)
		http.Error(w, "Failed to create document", http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"message": "Document created successfully"}`))
}

func getAsset(w http.ResponseWriter, r *http.Request) {
	enableCors(&w)

	vars := mux.Vars(r)
	id := vars["id"]

	res, err := esClient.Get("documents", id)
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

func updateAsset(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id := vars["id"]

	var doc Document
	if err := json.NewDecoder(r.Body).Decode(&doc); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	// Serialize the document to JSON for updating
	docBytes, _ := json.Marshal(doc)

	res, err := esClient.Update("documents", id, bytes.NewReader([]byte(`{"doc": `+string(docBytes)+`}`)))
	if err != nil {
		http.Error(w, "Failed to update document", http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message": "Document updated successfully"}`))
}

func deleteAsset(w http.ResponseWriter, r *http.Request) {
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

func listAssets(w http.ResponseWriter, r *http.Request) {
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
	var documents []Document
	for _, hit := range hits {
		doc := hit.(map[string]interface{})["_source"]
		jsonDoc, _ := json.Marshal(doc)
		var document Document
		json.Unmarshal(jsonDoc, &document)
		documents = append(documents, document)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(documents)
}
