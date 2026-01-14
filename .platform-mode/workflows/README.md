# Workflows Directory

This directory contains orchestrated command sequences and workflow definitions for complex platform engineering processes.

## Structure

- `discovery-to-delivery/` - End-to-end workflow orchestrations
- `templates/` - Reusable workflow patterns and templates
- `automations/` - Automated workflow trigger definitions
- `integrations/` - External system integration workflows

## Workflow Types

### Process Orchestration
- **Discovery → Analysis → Design** workflows for requirements gathering
- **Plan → Execute → Validate** workflows for implementation cycles  
- **Retrospect → Improve** workflows for continuous improvement

### Command Sequences
- **Epic Creation**: `/discovery` → `/analysis` → `/epic` → `/story`
- **Sprint Planning**: `/story` → `/estimate` → `/sprint-plan` → `/task-breakdown`
- **Implementation**: `/execute` → `/quality-gate` → `/acceptance-test` → `/validate`
- **Release**: `/demo-prep` → `/retrospect` → `/lessons-learned`

## Workflow Definition Structure

- **Trigger Conditions**: When this workflow should execute
- **Command Sequence**: Ordered list of slash commands and parameters
- **Decision Points**: Conditional branching based on outcomes
- **Quality Gates**: Validation checkpoints throughout the workflow
- **Rollback Procedures**: How to handle failures and rollbacks
- **Success Criteria**: Conditions for workflow completion

## Usage

Workflows enable complex, multi-step processes to be executed systematically with AI assistance while maintaining quality and consistency.