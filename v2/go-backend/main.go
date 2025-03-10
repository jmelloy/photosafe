package main

import (
	"crypto/tls"
	"log"
	"net/http"

	"github.com/elastic/go-elasticsearch/v8"
	"github.com/gorilla/mux"

	"go-backend/middleware"
	"go-backend/models"
	"go-backend/routes"
)

type Document models.Asset

var esClient *elasticsearch.Client

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
	router.Use(middleware.ElasticsearchMiddleware(esClient))
	router.Use(middleware.CORSMiddleware)
	router.Use(middleware.LoggingMiddleware)

	router.HandleFunc("/users", routes.CreateUser).Methods("POST")
	router.HandleFunc("/users/{id}", routes.GetUser).Methods("GET")
	router.HandleFunc("/users/{id}", routes.UpdateUser).Methods("PATCH")

	router.HandleFunc("/assets", routes.CreateAsset).Methods("POST")
	router.HandleFunc("/assets/{id}", routes.GetAsset).Methods("GET")
	router.HandleFunc("/assets/{id}/image", routes.GetAssetImage).Methods("GET")
	router.HandleFunc("/assets/{id}", routes.UpdateAsset).Methods("PATCH")
	router.HandleFunc("/assets/{id}", routes.DeleteAsset).Methods("DELETE")
	router.HandleFunc("/assets", routes.ListAssets).Methods("GET")

	log.Println("Server running on port 8080")
	log.Fatal(http.ListenAndServe(":8080", router))
}
