"""Tests for the orchestration agent and tools."""

from typing import Dict, Any, List
from data_collection_agent.graph.orchestration_agent import (
    create_orchestration_agent,
    run_orchestration_agent,
    orchestrate_data_collection
)
from data_collection_agent.tools.orchestration_tools import (
    DataCollectorTool,
    DataCollectorInput,
    DataCollectorOutput
)

def test_data_collector_tool():
    """Test the DataCollectorTool functionality."""
    # Create test data
    sources = ["source1", "source2"]
    criteria = {"quality_threshold": 0.7}
    
    ingestion_results = [
        {
            "status": "success",
            "output": {"data": "test data 1"}
        },
        {
            "status": "success",
            "output": {"data": "test data 2"}
        }
    ]
    
    reflection_results = [
        {
            "status": "success",
            "output": {"quality_score": 0.8}
        },
        {
            "status": "success",
            "output": {"quality_score": 0.9}
        }
    ]
    
    # Create and run the tool
    tool = DataCollectorTool()
    result = tool._run(
        sources=sources,
        criteria=criteria,
        ingestion_results=ingestion_results,
        reflection_results=reflection_results
    )
    
    # Verify the output structure
    assert "summary" in result
    assert "quality_metrics" in result
    assert "recommendations" in result
    
    # Verify specific values
    assert result["summary"]["total_sources"] == 2
    assert result["summary"]["successful_sources"] == 2
    assert result["quality_metrics"]["average_quality_score"] == 0.85
    assert result["quality_metrics"]["completion_rate"] == 1.0

def test_orchestration_agent():
    """Test the orchestration agent functionality."""
    # Create test data
    sources = ["source1", "source2"]
    criteria = {"quality_threshold": 0.7}
    
    # Run the orchestration agent
    result = run_orchestration_agent(
        tool_name="data_collector",
        input_data={
            "sources": sources,
            "criteria": criteria
        }
    )
    
    # Verify the output structure
    assert "output" in result
    assert "status" in result
    assert result["status"] == "success"

def test_orchestrate_data_collection():
    """Test the full data collection orchestration process."""
    # Create test data
    sources = ["source1", "source2"]
    evaluation_criteria = {"quality_threshold": 0.7}
    
    # Run the orchestration process
    result = orchestrate_data_collection(
        sources=sources,
        evaluation_criteria=evaluation_criteria
    )
    
    # Verify the output structure
    assert "output" in result
    assert "status" in result
    assert result["status"] == "success"

def test_data_collector_input_validation():
    """Test input validation for DataCollectorInput."""
    # Valid input
    valid_input = {
        "sources": ["source1"],
        "criteria": {"threshold": 0.7}
    }
    try:
        DataCollectorInput(**valid_input)
    except Exception as e:
        assert False, f"Valid input validation failed: {str(e)}"
    
    # Invalid input - missing required fields
    invalid_input = {"sources": ["source1"]}
    try:
        DataCollectorInput(**invalid_input)
        assert False, "Invalid input validation should have failed"
    except Exception:
        pass  # Expected to fail

def test_data_collector_output_validation():
    """Test output validation for DataCollectorOutput."""
    # Valid output
    valid_output = {
        "summary": {"total": 1},
        "quality_metrics": {"score": 0.8},
        "recommendations": ["test"]
    }
    try:
        DataCollectorOutput(**valid_output)
    except Exception as e:
        assert False, f"Valid output validation failed: {str(e)}"
    
    # Invalid output - missing required fields
    invalid_output = {"summary": {"total": 1}}
    try:
        DataCollectorOutput(**invalid_output)
        assert False, "Invalid output validation should have failed"
    except Exception:
        pass  # Expected to fail

if __name__ == "__main__":
    # Run all tests
    test_data_collector_tool()
    test_orchestration_agent()
    test_orchestrate_data_collection()
    test_data_collector_input_validation()
    test_data_collector_output_validation()
    
    print("All tests passed successfully!") 