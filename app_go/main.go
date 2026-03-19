package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
	"time"
)

type Service struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

type System struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
}

type Runtime struct {
	UptimeSeconds float64 `json:"uptime_seconds"`
	UptimeHuman   string  `json:"uptime_human"`
	CurrentTime   string  `json:"current_time"`
	Timezone      string  `json:"timezone"`
}

type RequestData struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

type Endpoint struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

type ServiceInfo struct {
	Service   Service     `json:"service"`
	System    System      `json:"system"`
	Runtime   Runtime     `json:"runtime"`
	Request   RequestData `json:"request"`
	Endpoints []Endpoint  `json:"endpoints"`
}

var startTime = time.Now()

func runHealthcheck(port string) error {
	client := &http.Client{Timeout: 2 * time.Second}
	request, err := http.NewRequest(http.MethodGet, "http://127.0.0.1:"+port+"/health", nil)
	if err != nil {
		return err
	}

	response, err := client.Do(request)
	if err != nil {
		return err
	}
	defer response.Body.Close()

	if response.StatusCode != http.StatusOK {
		return fmt.Errorf("unexpected status code: %d", response.StatusCode)
	}

	return nil
}

func getUptime() (float64, string) {
	duration := time.Since(startTime)
	seconds := duration.Seconds()

	hours := int(duration.Hours())
	minutes := int(duration.Minutes()) % 60

	human := fmt.Sprintf("%d hours, %d minutes", hours, minutes)
	return seconds, human
}

func mainHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Processing request for %s", r.URL.Path)

	// Handle only exact match for root path to avoid catch-all
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}

	hostname, _ := os.Hostname()
	uptimeSeconds, uptimeHuman := getUptime()

	info := ServiceInfo{
		Service: Service{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go/net/http",
		},
		System: System{
			Hostname:        hostname,
			Platform:        runtime.GOOS,
			PlatformVersion: "unknown",
			Architecture:    runtime.GOARCH,
			CPUCount:        runtime.NumCPU(),
		},
		Runtime: Runtime{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339),
			Timezone:      "UTC",
		},
		Request: RequestData{
			ClientIP:  r.RemoteAddr,
			UserAgent: r.UserAgent(),
			Method:    r.Method,
			Path:      r.URL.Path,
		},
		Endpoints: []Endpoint{
			{"/", "GET", "Service information"},
			{"/health", "GET", "Health check"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(info); err != nil {
		log.Printf("Error encoding response: %v", err)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Processing request for /health")

	uptimeSeconds, _ := getUptime()

	response := map[string]interface{}{
		"status":         "healthy",
		"timestamp":      time.Now().UTC().Format(time.RFC3339),
		"uptime_seconds": uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	if len(os.Args) > 1 && os.Args[1] == "--healthcheck" {
		if err := runHealthcheck(port); err != nil {
			log.Printf("Healthcheck failed: %v", err)
			os.Exit(1)
		}
		return
	}

	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	log.Printf("Starting server on port %s...", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}
