// Collaborative workflow: Coordinator delegates to sub-agents sharing state.
// Use when multiple specialized agents collaborate on shared context.
package main

import (
	"context"
	"fmt"
	"iter"
	"log"
	"os"

	"google.golang.org/genai"
	"google.golang.org/adk/agent"
	"google.golang.org/adk/model"
	"google.golang.org/adk/runner"
	"google.golang.org/adk/session"
)

func main() {
	ctx := context.Background()

	// Shared state for collaboration
	sharedState := make(map[string]string)

	// Create specialized workers
	researcher := createResearcher(sharedState)
	writer := createWriter(sharedState)
	reviewer := createReviewer(sharedState)

	// Coordinator orchestrates the collaboration
	coordinator := createCoordinator(sharedState, []agent.Agent{researcher, writer, reviewer})

	log.Printf("Collaborative workflow created: %s", coordinator.Name())
	fmt.Println("Workers: researcher, writer, reviewer")
	fmt.Println("Coordinator manages task delegation and state sharing")
}

func createCoordinator(state map[string]string, workers []agent.Agent) agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "coordinator",
		Description: "Orchestrates collaboration between specialized agents",
		SubAgents:   workers,
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Coordinator: Task analyzed. Delegating to specialized workers."}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}

func createResearcher(state map[string]string) agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "researcher",
		Description: "Researches topics and stores findings in shared state",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				state["research_findings"] = "Key findings from research phase"
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Research complete. Findings stored in shared state."}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}

func createWriter(state map[string]string) agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "writer",
		Description: "Writes content based on research findings from shared state",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				findings := state["research_findings"]
				draft := fmt.Sprintf("Draft based on: %s", findings)
				state["draft"] = draft
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: draft}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}

func createReviewer(state map[string]string) agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "reviewer",
		Description: "Reviews draft from shared state and provides feedback",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				draft := state["draft"]
				feedback := fmt.Sprintf("Review of draft: '%s' — approved with minor edits.", draft)
				state["review"] = feedback
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: feedback}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}
