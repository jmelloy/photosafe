package middleware

import (
	"context"
	"net/http"

	"github.com/elastic/go-elasticsearch/v8"
)

type contextKey string

const esClientKey contextKey = "esClient"

// ElasticsearchMiddleware injects the Elasticsearch client into the request context
func ElasticsearchMiddleware(es *elasticsearch.Client) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := context.WithValue(r.Context(), esClientKey, es)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// GetElasticsearchClient retrieves the Elasticsearch client from the request context
func GetElasticsearchClient(r *http.Request) *elasticsearch.Client {
	if es, ok := r.Context().Value(esClientKey).(*elasticsearch.Client); ok {
		return es
	}
	return nil
}
