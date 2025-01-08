package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"go-backend/models"
	"io/ioutil"
	"log"
	"net/http"
	"os"
)

type User models.User

func main() {
	// Define and parse the userID flag
	userID := flag.String("userID", "", "The userID to fetch from the API")
	apiURL := flag.String("url", "http://localhost:8080/users", "The API URL for user creation")
	flag.Parse()

	// Validate the userID argument
	if *userID == "" {
		fmt.Println("Error: userID is required.")
		flag.Usage()
		os.Exit(1)
	}

	// Create the request body
	requestBody, err := json.Marshal(map[string]string{
		"ID": *userID,
	})
	if err != nil {
		fmt.Printf("Error creating request body: %v\n", err)
		os.Exit(1)
	}

	// Make the POST request
	resp, err := http.Post(*apiURL, "application/json", bytes.NewBuffer(requestBody))
	if err != nil {
		fmt.Printf("Error making request to API: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	// Check for non-200 HTTP status codes
	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		fmt.Printf("Error: API returned status %d\n", resp.StatusCode)
		os.Exit(1)
	}
	log.Print(resp)
	// Read the response body
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("Error reading response: %v\n", err)
		os.Exit(1)
	}

	// Parse the JSON response into a User struct
	var user User
	err = json.Unmarshal(body, &user)
	if err != nil {
		fmt.Printf("Error parsing response JSON: %v\n", err)
		os.Exit(1)
	}

	// Print the user details
	fmt.Printf("User Details:\n")
	fmt.Printf("ID: %s\n", user.ID)
	fmt.Printf("Created: %s\n", user.CreatedAt)
	fmt.Printf("Token: %s\n", user.Token)
}
