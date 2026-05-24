package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"time"
)

const defaultTimeout = 30 * time.Second

func checkInstagram(target string, timeout time.Duration) (int, error) {
	client := &http.Client{
		Timeout: timeout,
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return http.ErrUseLastResponse
		},
	}

	url := fmt.Sprintf("https://www.instagram.com/%s/", target)
	resp, err := client.Get(url)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	return resp.StatusCode, nil
}

func main() {
	target := os.Getenv("INSTAGRAM_USERNAME")
	if target == "" {
		log.Fatal("INSTAGRAM_USERNAME environment variable is required")
	}

	timeout := defaultTimeout
	if t := os.Getenv("HTTP_TIMEOUT"); t != "" {
		var err error
		timeout, err = time.ParseDuration(t)
		if err != nil {
			log.Fatalf("Invalid HTTP_TIMEOUT: %v", err)
		}
	}

	log.Printf("Checking Instagram profile: %s", target)

	statusCode, err := checkInstagram(target, timeout)
	if err != nil {
		log.Fatalf("Error checking profile %s: %v", target, err)
	}

	switch statusCode {
	case http.StatusOK:
		log.Printf("Profile '%s' is available (status: %d)", target, statusCode)
	case http.StatusNotFound:
		log.Printf("Profile '%s' is NOT available (status: %d)", target, statusCode)
	case http.StatusForbidden:
		log.Printf("Profile '%s' may be private or blocked (status: %d)", target, statusCode)
	default:
		log.Printf("Profile '%s' returned unexpected status: %d", target, statusCode)
	}

	if statusCode != http.StatusOK {
		os.Exit(1)
	}
}
