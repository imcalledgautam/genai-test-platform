#!/usr/bin/env python3
"""
Human-in-the-Loop (HITL) Validation Workflow
============================================

Manages human review and approval process for LLM-generated tests.
Creates structured review artifacts and enforces quality gates before
allowing tests to be merged into the main codebase.

Workflow:
1. LLM generates tests → temp branch
2. Creates review artifact with context and checklist
3. Human reviewer validates against criteria
4. Only approved tests get merged
"""

import json
import pathlib
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

ROOT = pathlib.Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "genai_artifacts"

@dataclass
class ReviewItem:
    """Represents a single item for human review."""
    file_path: str
    test_type: str  # "unit", "integration", "e2e"
    target_function: str
    generated_content: str
    context: Dict[str, Any]
    checklist_items: List[str]
    status: str = "pending"  # "pending", "approved", "rejected"
    reviewer_notes: str = ""
    timestamp: str = ""

class HITLValidator:
    """Human-in-the-Loop validation orchestrator."""
    
    def __init__(self):
        self.artifacts_dir = ARTIFACTS
        self.artifacts_dir.mkdir(exist_ok=True)
        
    def create_review_artifact(self, 
                             generated_tests: List[Dict[str, Any]],
                             context: Dict[str, Any]) -> str:
        """Create a structured review artifact for human validation."""
        
        review_items = []
        
        for test_info in generated_tests:
            # Extract test details
            file_path = test_info.get("file_path", "")
            content = test_info.get("content", "")
            target = test_info.get("target_function", "")
            test_type = test_info.get("type", "unit")
            
            # Generate review checklist
            checklist = self._generate_checklist(test_type, target, content)
            
            review_item = ReviewItem(
                file_path=file_path,
                test_type=test_type,
                target_function=target,
                generated_content=content,
                context={
                    "stack": context.get("stack", "unknown"),
                    "framework": context.get("framework", "unknown"),
                    "source_file": test_info.get("source_file", ""),
                    "function_signature": test_info.get("signature", "")
                },
                checklist_items=checklist,
                timestamp=datetime.utcnow().isoformat() + "Z"
            )
            
            review_items.append(review_item)
        
        # Create review artifact
        review_artifact = {
            "id": f"review_{int(datetime.utcnow().timestamp())}",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "status": "pending_review",
            "repository_context": {
                "stack": context.get("stack"),
                "total_files": len(generated_tests),
                "context_file": str(context.get("context_file", "")),
                "generation_method": "llm_assisted"
            },
            "review_items": [asdict(item) for item in review_items],
            "review_criteria": self._get_review_criteria(),
            "approval_required": True,
            "reviewer": None,
            "approved_at": None
        }
        
        # Save artifact
        artifact_path = self.artifacts_dir / f"hitl_review_{review_artifact['id']}.json"
        artifact_path.write_text(json.dumps(review_artifact, indent=2))
        
        # Create human-readable review file
        self._create_human_review_file(review_artifact, artifact_path.with_suffix('.md'))
        
        return str(artifact_path)
    
    def _generate_checklist(self, test_type: str, target_function: str, content: str) -> List[str]:
        """Generate review checklist based on test type and content."""
        
        base_checklist = [
            "✅ Test targets the correct function/class",
            "✅ Test name is descriptive and follows naming conventions",
            "✅ Test is deterministic (no sleep, random, network calls)",
            "✅ Test is properly isolated (no shared state)",
            "✅ Assertions are specific and meaningful",
            "✅ Edge cases are covered (null, empty, boundary values)",
            "✅ Error conditions are tested appropriately",
            "✅ Test follows AAA pattern (Arrange, Act, Assert)",
            "✅ External dependencies are properly mocked",
            "✅ Test imports are correct and minimal"
        ]
        
        # Add type-specific checks
        if test_type == "unit":
            base_checklist.extend([
                "✅ Test focuses on single unit of functionality",
                "✅ No external system dependencies",
                "✅ Fast execution (< 1 second)"
            ])
        elif test_type == "integration":
            base_checklist.extend([
                "✅ Tests interaction between components",
                "✅ Uses appropriate test fixtures",
                "✅ Cleans up resources after test"
            ])
        elif test_type == "e2e":
            base_checklist.extend([
                "✅ Tests complete user workflow",
                "✅ Uses appropriate test data",
                "✅ Handles async operations correctly"
            ])
        
        # Add content-specific checks
        if "async" in content:
            base_checklist.append("✅ Async operations are properly awaited")
        
        if "mock" in content.lower():
            base_checklist.append("✅ Mocks are configured correctly")
        
        if "parametrize" in content:
            base_checklist.append("✅ Parametrized tests cover meaningful scenarios")
        
        return base_checklist
    
    def _get_review_criteria(self) -> Dict[str, Any]:
        """Get standardized review criteria."""
        return {
            "must_have": [
                "Deterministic behavior",
                "Proper isolation",
                "Clear assertions",
                "Correct imports",
                "Valid syntax"
            ],
            "should_have": [
                "Descriptive test names",
                "Edge case coverage", 
                "Error condition testing",
                "Appropriate mocking",
                "AAA pattern structure"
            ],
            "nice_to_have": [
                "Performance considerations",
                "Comprehensive documentation",
                "Parametrized test cases",
                "Custom fixtures"
            ],
            "automatic_reject": [
                "Uses sleep() or delays",
                "Makes real network calls",
                "Has syntax errors",
                "Missing assertions",
                "Accesses real filesystem",
                "Uses random() without seed"
            ]
        }
    
    def _create_human_review_file(self, review_artifact: Dict[str, Any], output_path: pathlib.Path):
        """Create a human-readable Markdown review file."""
        
        content = f"""# Test Review: {review_artifact['id']}

## Repository Context
- **Stack**: {review_artifact['repository_context']['stack']}
- **Total Files**: {review_artifact['repository_context']['total_files']}
- **Generation Method**: {review_artifact['repository_context']['generation_method']}
- **Created**: {review_artifact['created_at']}

## Review Status: {review_artifact['status'].upper()}

---

## Review Items

"""
        
        for i, item in enumerate(review_artifact['review_items'], 1):
            content += f"""### {i}. {item['file_path']}

**Target**: `{item['target_function']}` ({item['test_type']} test)
**Status**: {item['status']}

#### Generated Code:
```python
{item['generated_content']}
```

#### Review Checklist:
"""
            for check in item['checklist_items']:
                content += f"- [ ] {check}\n"
            
            content += f"""
#### Reviewer Notes:
```
{item.get('reviewer_notes', '(No notes yet)')}
```

---

"""
        
        content += f"""## Review Criteria

### Must Have (Auto-Reject if Missing):
"""
        for criterion in review_artifact['review_criteria']['automatic_reject']:
            content += f"- ❌ **NO** {criterion}\n"
        
        content += "\n### Required:\n"
        for criterion in review_artifact['review_criteria']['must_have']:
            content += f"- ✅ {criterion}\n"
        
        content += "\n### Recommended:\n"
        for criterion in review_artifact['review_criteria']['should_have']:
            content += f"- ⚠️ {criterion}\n"
        
        content += f"""

## Reviewer Instructions

1. **Review each test** against the checklist items
2. **Mark items** as complete by changing `[ ]` to `[x]`
3. **Add notes** in the "Reviewer Notes" sections
4. **Update status** for each item: `pending` → `approved` or `rejected`
5. **Run the approval command** when ready:

```bash
python tools/hitl_validator_v2.py approve {review_artifact['id']} --reviewer "Your Name"
```

## Auto-Validation Results

Run policy checker on generated tests:
```bash
python tools/policy_checker_v2.py tests/generated/ --format json > policy_check.json
```

---
*Generated by GenAI Test Platform HITL Validator*
"""
        
        output_path.write_text(content)
        print(f"📋 Human review file created: {output_path}")
    
    def approve_review(self, review_id: str, reviewer_name: str, 
                      approved_items: Optional[List[str]] = None) -> bool:
        """Approve a review and update the artifact."""
        
        artifact_path = self.artifacts_dir / f"hitl_review_{review_id}.json"
        
        if not artifact_path.exists():
            print(f"❌ Review artifact not found: {artifact_path}")
            return False
        
        try:
            # Load current artifact
            artifact = json.loads(artifact_path.read_text())
            
            # Update approval status
            artifact["status"] = "approved"
            artifact["reviewer"] = reviewer_name
            artifact["approved_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Update individual items if specified
            if approved_items:
                for item in artifact["review_items"]:
                    if item["file_path"] in approved_items:
                        item["status"] = "approved"
            else:
                # Approve all items
                for item in artifact["review_items"]:
                    item["status"] = "approved"
            
            # Save updated artifact
            artifact_path.write_text(json.dumps(artifact, indent=2))
            
            print(f"✅ Review {review_id} approved by {reviewer_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error approving review: {e}")
            return False
    
    def reject_review(self, review_id: str, reviewer_name: str, reason: str) -> bool:
        """Reject a review with reason."""
        
        artifact_path = self.artifacts_dir / f"hitl_review_{review_id}.json"
        
        if not artifact_path.exists():
            print(f"❌ Review artifact not found: {artifact_path}")
            return False
        
        try:
            # Load and update artifact
            artifact = json.loads(artifact_path.read_text())
            artifact["status"] = "rejected" 
            artifact["reviewer"] = reviewer_name
            artifact["rejection_reason"] = reason
            artifact["reviewed_at"] = datetime.utcnow().isoformat() + "Z"
            
            # Reject all items
            for item in artifact["review_items"]:
                item["status"] = "rejected"
                item["reviewer_notes"] = reason
            
            artifact_path.write_text(json.dumps(artifact, indent=2))
            
            print(f"❌ Review {review_id} rejected by {reviewer_name}")
            print(f"   Reason: {reason}")
            return True
            
        except Exception as e:
            print(f"❌ Error rejecting review: {e}")
            return False
    
    def list_pending_reviews(self) -> List[Dict[str, Any]]:
        """List all pending reviews."""
        
        pending_reviews = []
        
        for artifact_file in self.artifacts_dir.glob("hitl_review_*.json"):
            try:
                artifact = json.loads(artifact_file.read_text())
                if artifact.get("status") == "pending_review":
                    pending_reviews.append({
                        "id": artifact["id"],
                        "created_at": artifact["created_at"],
                        "files_count": len(artifact["review_items"]),
                        "stack": artifact["repository_context"]["stack"]
                    })
            except Exception:
                continue
        
        return pending_reviews
    
    def get_review_status(self, review_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific review."""
        
        artifact_path = self.artifacts_dir / f"hitl_review_{review_id}.json"
        
        if not artifact_path.exists():
            return None
        
        try:
            artifact = json.loads(artifact_path.read_text())
            
            # Calculate summary
            total_items = len(artifact["review_items"])
            approved_items = sum(1 for item in artifact["review_items"] 
                               if item["status"] == "approved")
            rejected_items = sum(1 for item in artifact["review_items"]
                               if item["status"] == "rejected") 
            
            return {
                "id": review_id,
                "status": artifact["status"],
                "total_items": total_items,
                "approved_items": approved_items,
                "rejected_items": rejected_items,
                "pending_items": total_items - approved_items - rejected_items,
                "reviewer": artifact.get("reviewer"),
                "created_at": artifact["created_at"]
            }
            
        except Exception:
            return None

def main():
    """CLI entry point for HITL validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Human-in-the-Loop test validation")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List pending reviews
    subparsers.add_parser("list", help="List pending reviews")
    
    # Approve review
    approve_parser = subparsers.add_parser("approve", help="Approve a review")
    approve_parser.add_argument("review_id", help="Review ID to approve")
    approve_parser.add_argument("--reviewer", "-r", required=True, help="Reviewer name")
    approve_parser.add_argument("--files", nargs="*", help="Specific files to approve")
    
    # Reject review
    reject_parser = subparsers.add_parser("reject", help="Reject a review")
    reject_parser.add_argument("review_id", help="Review ID to reject")
    reject_parser.add_argument("--reviewer", "-r", required=True, help="Reviewer name")
    reject_parser.add_argument("--reason", required=True, help="Rejection reason")
    
    # Status check
    status_parser = subparsers.add_parser("status", help="Check review status")
    status_parser.add_argument("review_id", help="Review ID to check")
    
    args = parser.parse_args()
    
    validator = HITLValidator()
    
    if args.command == "list":
        pending = validator.list_pending_reviews()
        if pending:
            print("📋 Pending Reviews:")
            print("-" * 60)
            for review in pending:
                print(f"ID: {review['id']}")
                print(f"Created: {review['created_at']}")
                print(f"Files: {review['files_count']}")
                print(f"Stack: {review['stack']}")
                print()
        else:
            print("✅ No pending reviews")
    
    elif args.command == "approve":
        success = validator.approve_review(args.review_id, args.reviewer, args.files)
        sys.exit(0 if success else 1)
    
    elif args.command == "reject":
        success = validator.reject_review(args.review_id, args.reviewer, args.reason)
        sys.exit(0 if success else 1)
    
    elif args.command == "status":
        status = validator.get_review_status(args.review_id)
        if status:
            print(f"📊 Review Status: {status['id']}")
            print(f"Status: {status['status']}")
            print(f"Items: {status['approved_items']}/{status['total_items']} approved")
            if status['rejected_items'] > 0:
                print(f"Rejected: {status['rejected_items']}")
            if status.get('reviewer'):
                print(f"Reviewer: {status['reviewer']}")
        else:
            print(f"❌ Review not found: {args.review_id}")
            sys.exit(1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()