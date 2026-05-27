// Parallel template: fan-out to multiple workers using ParallelAgent.
// All sub-agents run concurrently. Results aggregated after all complete.
package main

import (
	"fmt"
	"iter"
	"log"
	"time"

	"google.golang.org/genai"
	"google.golang.org/adk/agent"
	"google.golang.org/adk/agent/workflowagents/parallelagent"
	"google.golang.org/adk/model"
	"google.golang.org/adk/session"
)

func main() {
	// Worker 1: Web search (simulated with delay)
	webSearch, _ := agent.New(agent.Config{
		Name:        "web_search",
		Description: "Searches web for information",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				time.Sleep(200 * time.Millisecond) // Simulate network call
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Web results: 15 relevant articles found."}},
						},
					},
				}, nil)
			}
		},
	})

	// Worker 2: Database query (simulated with delay)
	dbQuery, _ := agent.New(agent.Config{
		Name:        "db_query",
		Description: "Queries internal database",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				time.Sleep(100 * time.Millisecond) // Simulate DB call
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "DB results: 3 matching records in customers table."}},
						},
					},
				}, nil)
			}
		},
	})

	// Worker 3: API call (simulated with delay)
	apiCall, _ := agent.New(agent.Config{
		Name:        "api_call",
		Description: "Calls external API for enrichment",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				time.Sleep(150 * time.Millisecond) // Simulate API call
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "API results: customer profiles enriched with external data."}},
						},
					},
				}, nil)
			}
		},
	})

	// Build parallel fan-out: all three workers run concurrently
	fanOut, err := parallelagent.New(parallelagent.Config{
		AgentConfig: agent.Config{
			Name:        "multi_source_search",
			Description: "Concurrently searches web, DB, and API",
			SubAgents:   []agent.Agent{webSearch, dbQuery, apiCall},
		},
	})
	if err != nil {
		log.Fatalf("Failed to create parallel agent: %v", err)
	}

	fmt.Printf("Parallel workflow created: %s\n", fanOut.Name())
	fmt.Println("Workers (run concurrently): web_search, db_query, api_call")
	fmt.Println("Total wall time ≈ max(200ms, 100ms, 150ms) = 200ms")
}
