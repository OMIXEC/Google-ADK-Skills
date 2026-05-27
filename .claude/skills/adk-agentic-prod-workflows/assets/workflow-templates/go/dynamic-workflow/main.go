// Dynamic workflow: agents created programmatically based on runtime input.
// Use when workflow shape depends on data, not known at compile time.
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

// WorkflowState carries runtime state across dynamically created agents.
type WorkflowState struct {
	CorrelationID string
	Input         string
	AgentChain    []string
	Results       map[string]string
	Errors        []string
}

// DynamicWorkflow creates agents at runtime based on input classification.
type DynamicWorkflow struct {
	state *WorkflowState
}

func NewDynamicWorkflow(correlationID string) *DynamicWorkflow {
	return &DynamicWorkflow{
		state: &WorkflowState{
			CorrelationID: correlationID,
			Results:       make(map[string]string),
			AgentChain:    []string{},
		},
	}
}

// BuildAgents analyzes input and creates the appropriate agent chain.
func (dw *DynamicWorkflow) BuildAgents(ctx context.Context, userInput string) ([]agent.Agent, error) {
	dw.state.Input = userInput

	// Classify the input to determine required agents
	category := classifyInput(userInput)
	log.Printf("[%s] Input classified as: %s", dw.state.CorrelationID, category)

	var agents []agent.Agent

	switch category {
	case "analysis":
		agents = append(agents, dw.createDataCollector())
		agents = append(agents, dw.createAnalyzer())
		agents = append(agents, dw.createReportGenerator())
	case "qa":
		agents = append(agents, dw.createRetriever())
		agents = append(agents, dw.createAnswerGenerator())
	default:
		agents = append(agents, dw.createGeneralAssistant())
	}

	for _, a := range agents {
		dw.state.AgentChain = append(dw.state.AgentChain, a.Name())
	}

	return agents, nil
}

func classifyInput(input string) string {
	// Heuristic classification — replace with LLM-based in production
	if len(input) > 200 {
		return "analysis"
	}
	return "qa"
}

func (dw *DynamicWorkflow) createDataCollector() agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "data_collector",
		Description: "Collects relevant data for analysis",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Data collected: relevant sources identified."}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}

func (dw *DynamicWorkflow) createAnalyzer() agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "analyzer",
		Description: "Analyzes collected data for insights",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Analysis complete: key patterns identified."}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}

func (dw *DynamicWorkflow) createReportGenerator() agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "report_generator",
		Description: "Generates final report from analysis",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Report generated: findings summarized."}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}

func (dw *DynamicWorkflow) createRetriever() agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "retriever",
		Description: "Retrieves relevant information for answering",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Relevant documents retrieved."}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}

func (dw *DynamicWorkflow) createAnswerGenerator() agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "answer_generator",
		Description: "Generates answer from retrieved context",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Answer generated from retrieved context."}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}

func (dw *DynamicWorkflow) createGeneralAssistant() agent.Agent {
	a, _ := agent.New(agent.Config{
		Name:        "general_assistant",
		Description: "Handles general queries",
		Run: func(ctx agent.InvocationContext) iter.Seq2[*session.Event, error] {
			return func(yield func(*session.Event, error) bool) {
				yield(&session.Event{
					LLMResponse: model.LLMResponse{
						Content: &genai.Content{
							Parts: []*genai.Part{{Text: "Query processed by general assistant."}},
						},
					},
				}, nil)
			}
		},
	})
	return a
}

func main() {
	ctx := context.Background()
	correlationID := os.Getenv("CORRELATION_ID")
	if correlationID == "" {
		correlationID = "dynamic-workflow-1"
	}

	wf := NewDynamicWorkflow(correlationID)

	userInput := os.Getenv("USER_INPUT")
	if userInput == "" {
		userInput = "Analyze recent market trends and generate a report"
	}

	agents, err := wf.BuildAgents(ctx, userInput)
	if err != nil {
		log.Fatalf("Failed to build agents: %v", err)
	}

	fmt.Printf("Dynamic workflow [%s] created with %d agents:\n", correlationID, len(agents))
	for i, a := range agents {
		fmt.Printf("  %d. %s — %s\n", i+1, a.Name(), a.Description())
	}
	fmt.Printf("\nAgent chain: %v\n", wf.state.AgentChain)
}
