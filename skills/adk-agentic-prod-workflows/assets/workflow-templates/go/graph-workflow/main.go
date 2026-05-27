// Graph workflow template (Go)
// Pattern: DAG with nodes, edges, and conditions.
// Each node wraps an agent call. Edges define transitions.

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"time"

	"github.com/google/uuid"
)

// ── UserContext ──────────────────────────────────────────────────

type UserContext struct {
	UserID       string   `json:"user_id"`
	AuthProvider string   `json:"auth_provider"`
	Roles        []string `json:"roles"`
	Scopes       []string `json:"scopes"`
	TenantID     string   `json:"tenant_id,omitempty"`
}

// ── Tool definitions ─────────────────────────────────────────────

type ValidateInput struct {
	Data       map[string]any `json:"data"`
	SchemaName string         `json:"schema_name"`
}

type ValidateOutput struct {
	IsValid        bool            `json:"is_valid"`
	Errors         []string        `json:"errors"`
	SanitizedData  map[string]any  `json:"sanitized_data,omitempty"`
}

func validateInput(ctx context.Context, input ValidateInput) (ValidateOutput, error) {
	slog.Info("tool_call", "tool", "validate_input", "schema", input.SchemaName)
	if input.Data == nil {
		return ValidateOutput{
			IsValid: false,
			Errors:  []string{"Input data is empty"},
		}, nil
	}
	return ValidateOutput{
		IsValid:       true,
		Errors:        nil,
		SanitizedData: input.Data,
	}, nil
}

type ProcessData struct {
	Data      map[string]any `json:"data"`
	Operation string         `json:"operation"`
}

type ProcessOutput struct {
	Status string          `json:"status"`
	Result map[string]any  `json:"result,omitempty"`
	Error  string          `json:"error,omitempty"`
}

func processData(ctx context.Context, input ProcessData) (ProcessOutput, error) {
	slog.Info("tool_call", "tool", "process_data", "operation", input.Operation)
	return ProcessOutput{
		Status: "ok",
		Result: input.Data,
	}, nil
}

// ── Agent ────────────────────────────────────────────────────────

type AgentConfig struct {
	Name        string
	Model       string
	Instruction string
}

type Agent struct {
	Config AgentConfig
}

func NewAgent(cfg AgentConfig) *Agent {
	return &Agent{Config: cfg}
}

func (a *Agent) Run(ctx context.Context, query string, state map[string]any) (map[string]any, error) {
	slog.Info("agent_run", "agent", a.Config.Name, "query", query)
	// In production: call ADK Go SDK or model API here
	// For now, return structured result
	return map[string]any{
		"ok":      true,
		"agent":   a.Config.Name,
		"query":   query,
	}, nil
}

// ── Workflow Graph ───────────────────────────────────────────────

type Condition func(state map[string]any) bool

type Node struct {
	ID    string
	Agent *Agent
}

type Edge struct {
	Source    string
	Target    string
	Condition Condition
}

type Workflow struct {
	Name       string
	Nodes      []Node
	Edges      []Edge
	EntryPoint string
	State      map[string]any
	UserCtx    UserContext
}

func NewGraphWorkflow(userCtx UserContext) *Workflow {
	return &Workflow{
		Name: "graph_workflow",
		Nodes: []Node{
			{ID: "validate", Agent: NewAgent(AgentConfig{
				Name: "validator", Model: "gemini-2.5-flash",
				Instruction: "Validate and sanitize input data.",
			})},
			{ID: "process", Agent: NewAgent(AgentConfig{
				Name: "processor", Model: "gemini-2.5-flash",
				Instruction: "Process validated data.",
			})},
			{ID: "fallback", Agent: NewAgent(AgentConfig{
				Name: "fallback", Model: "gemini-2.5-flash",
				Instruction: "Handle validation failures.",
			})},
		},
		Edges: []Edge{
			{
				Source: "validate", Target: "process",
				Condition: func(state map[string]any) bool {
					valid, _ := state["is_valid"].(bool)
					return valid
				},
			},
			{
				Source: "validate", Target: "fallback",
				Condition: func(state map[string]any) bool {
					valid, _ := state["is_valid"].(bool)
					return !valid
				},
			},
		},
		EntryPoint: "validate",
		State:      make(map[string]any),
		UserCtx:    userCtx,
	}
}

func (w *Workflow) Run(ctx context.Context, query string) error {
	correlationID := uuid.New().String()[:12]
	slog.Info("workflow_start",
		"correlation_id", correlationID,
		"user_id", w.UserCtx.UserID,
		"query", query,
	)

	start := time.Now()
	currentNodeID := w.EntryPoint

	for currentNodeID != "" {
		node := w.findNode(currentNodeID)
		if node == nil {
			return fmt.Errorf("node not found: %s", currentNodeID)
		}

		nodeStart := time.Now()
		result, err := node.Agent.Run(ctx, query, w.State)
		if err != nil {
			slog.Error("node_error",
				"node", currentNodeID,
				"error", err,
				"correlation_id", correlationID,
			)
			return fmt.Errorf("node %s: %w", currentNodeID, err)
		}

		// Merge node result into workflow state
		for k, v := range result {
			w.State[k] = v
		}

		slog.Info("node_complete",
			"node", currentNodeID,
			"latency_ms", time.Since(nodeStart).Milliseconds(),
			"correlation_id", correlationID,
		)

		currentNodeID = w.nextNode(currentNodeID)
	}

	slog.Info("workflow_complete",
		"correlation_id", correlationID,
		"latency_ms", time.Since(start).Milliseconds(),
	)
	return nil
}

func (w *Workflow) findNode(id string) *Node {
	for i := range w.Nodes {
		if w.Nodes[i].ID == id {
			return &w.Nodes[i]
		}
	}
	return nil
}

func (w *Workflow) nextNode(currentID string) string {
	for _, edge := range w.Edges {
		if edge.Source == currentID {
			if edge.Condition == nil || edge.Condition(w.State) {
				return edge.Target
			}
		}
	}
	return ""
}

// ── Entrypoint ───────────────────────────────────────────────────

func main() {
	ctx := context.Background()

	// UserContext injected from auth middleware
	userCtx := UserContext{
		UserID:       "user-123",
		AuthProvider: "firebase",
		Roles:        []string{"user"},
		Scopes:       []string{"read", "write"},
	}

	wf := NewGraphWorkflow(userCtx)
	if err := wf.Run(ctx, "Process order #12345"); err != nil {
		slog.Error("workflow failed", "error", err)
		os.Exit(1)
	}

	// Print state for debugging
	stateJSON, _ := json.MarshalIndent(wf.State, "", "  ")
	fmt.Printf("Workflow state: %s\n", stateJSON)
}
