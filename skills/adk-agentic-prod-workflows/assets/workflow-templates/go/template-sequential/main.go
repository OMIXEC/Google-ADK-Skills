// Sequential template: fixed-order pipeline using SequentialAgent.
// Writer → Reviewer → Publisher chain. Each stage processes output from previous.
package main

import (
	"fmt"
	"iter"
	"log"

	"google.golang.org/genai"
	"google.golang.org/adk/agent"
	"google.golang.org/adk/agent/workflowagents/sequentialagent"
	"google.golang.org/adk/model"
	"google.golang.org/adk/session"
)

func main() {
	// Step 1: Writer agent
	writer, _ := agent.New(agent.Config{
		Name:        "writer",
		Description: "Writes the initial draft",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Draft: This is the initial document draft with all required sections."}},
						},
					},
				}, nil)
			}
		},
	})

	// Step 2: Reviewer agent
	reviewer, _ := agent.New(agent.Config{
		Name:        "reviewer",
		Description: "Reviews the draft for quality and correctness",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Review: Draft quality is good. Minor edits suggested in section 3."}},
						},
					},
				}, nil)
			}
		},
	})

	// Step 3: Publisher agent
	publisher, _ := agent.New(agent.Config{
		Name:        "publisher",
		Description: "Finalizes and publishes the reviewed content",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Published: Content finalized and deployed. Publication ID: pub-2026-001"}},
						},
					},
				}, nil)
			}
		},
	})

	// Build sequential pipeline: Writer → Reviewer → Publisher
	pipeline, err := sequentialagent.New(sequentialagent.Config{
		AgentConfig: agent.Config{
			Name:        "content_pipeline",
			Description: "Sequential content pipeline: Write → Review → Publish",
			SubAgents:   []agent.Agent{writer, reviewer, publisher},
		},
	})
	if err != nil {
		log.Fatalf("Failed to create sequential pipeline: %v", err)
	}

	fmt.Printf("Sequential pipeline created: %s\n", pipeline.Name())
	fmt.Println("Pipeline stages: writer → reviewer → publisher")
}
