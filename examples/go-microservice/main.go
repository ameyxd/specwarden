package main

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

const serviceVersion = "0.4.0"

type healthResponse struct {
	Status string `json:"status"`
}

type versionResponse struct {
	Version string `json:"version"`
}

type item struct {
	ID   int    `json:"id"`
	Name string `json:"name"`
}

var items = []item{
	{ID: 1, Name: "widget"},
	{ID: 2, Name: "gadget"},
}

func main() {
	r := chi.NewRouter()
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)

	r.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(healthResponse{Status: "ok"})
	})

	r.Get("/version", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(versionResponse{Version: serviceVersion})
	})

	r.Get("/items", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(items)
	})

	log.Println("listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", r))
}
