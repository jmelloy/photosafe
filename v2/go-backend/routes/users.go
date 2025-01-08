package routes

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strings"
	"time"

	"go-backend/middleware"
	"go-backend/models"
	"go-backend/utils"

	"github.com/elastic/go-elasticsearch/v8"
	"github.com/gorilla/mux"
)

type User models.User

// GetUsers handles the /api/users endpoint
func GetUser(w http.ResponseWriter, r *http.Request) {
	esClient := middleware.GetElasticsearchClient(r)

	vars := mux.Vars(r)
	id := vars["id"]

	res, err := esClient.Get("users", id)
	if err != nil {
		http.Error(w, "Failed to fetch document", http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	if res.IsError() {
		log.Print(res)
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	var user User
	if err := json.NewDecoder(res.Body).Decode(&user); err != nil {
		http.Error(w, "Error parsing response", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(user)
}

func CreateUser(w http.ResponseWriter, r *http.Request) {
	esClient := middleware.GetElasticsearchClient(r)

	var user User
	if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
		log.Print(err)
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	// Serialize the document to JSON for indexing
	userBytes, _ := json.Marshal(user)

	if user.Token == "" {
		user.Token = utils.GenerateUUIDv7("tok")
	}

	user.CreatedAt = time.Now().Format(time.RFC3339)

	res, err := esClient.Index(
		"users", // Index name
		bytes.NewReader(userBytes),
		esClient.Index.WithDocumentID(user.ID),
	)

	if err != nil {
		log.Print(err)
		http.Error(w, "Failed to fetch user", http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	if res.IsError() {
		log.Print(res)
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"message": "User created successfully"}`))
}

func UpdateUser(w http.ResponseWriter, r *http.Request) {
	esClient := middleware.GetElasticsearchClient(r)

	vars := mux.Vars(r)
	id := vars["id"]

	var user User
	if err := json.NewDecoder(r.Body).Decode(&user); err != nil {
		log.Print(err)
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}

	// Serialize the document to JSON for indexing
	userBytes, _ := json.Marshal(user)

	res, err := esClient.Index(
		"users", // Index name
		bytes.NewReader(userBytes),
		esClient.Index.WithDocumentID(id),
	)

	if err != nil {
		log.Print(err)
		http.Error(w, "Failed to fetch user", http.StatusInternalServerError)
		return
	}
	defer res.Body.Close()

	if res.IsError() {
		log.Print(res)
		http.Error(w, "User not found", http.StatusNotFound)
		return
	}

	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"message": "User updated successfully"}`))
}

// AuthenticateUserFromToken checks if the token exists and is valid in Elasticsearch
func AuthenticateUserFromToken(r *http.Request, esClient *elasticsearch.Client) (*User, error) {
	authHeader := r.Header.Get("Authorization")
	if authHeader == "" {
		return nil, fmt.Errorf("Authorization header is missing")
	}

	// Split the header into "Bearer" and the token
	parts := strings.Fields(authHeader)
	if len(parts) != 2 || parts[0] != "Bearer" {
		return nil, fmt.Errorf("Authorization header format must be Bearer {token}")
	}

	token := parts[1]

	// Elasticsearch query to find the token document
	query := fmt.Sprintf(`{
		"query": {
			"term": {
				"token.keyword": {
					"value": "%s"
				}
			}
		}
	}`, token)

	// Send the query to Elasticsearch
	resp, err := esClient.Search(
		esClient.Search.WithIndex("users"),
		esClient.Search.WithBody(bytes.NewReader([]byte(query))),
		esClient.Search.WithTrackTotalHits(true),
	)
	if err != nil {
		return nil, fmt.Errorf("error querying Elasticsearch: %s", err)
	}
	defer resp.Body.Close()

	// Check if the token exists and is valid
	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("error parsing Elasticsearch response: %s", err)
	}

	// Check if the token exists and is valid
	if hits, found := result["hits"].(map[string]interface{})["hits"].([]interface{}); found && len(hits) > 0 {
		// Token exists, retrieve user details
		if source, ok := hits[0].(map[string]interface{})["_source"].(map[string]interface{}); ok {

			jsonDoc, _ := json.Marshal(source)
			var user *User
			json.Unmarshal(jsonDoc, &user)

			return user, nil
		}
	}
	return nil, nil // Token not found or invalid

}
