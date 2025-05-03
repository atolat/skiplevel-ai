from data_collection_pipeline import data_pipeline_chain

def main():
    # Example query
    test_query = "Find the latest public documents on engineering promotion rubrics at top tech companies"
    
    # Run the pipeline
    print("Starting pipeline...")
    print(f"Query: {test_query}\n")
    print("Pipeline graph:")
    print(data_pipeline_chain.get_graph().print_ascii())
    
    for step in data_pipeline_chain.stream(test_query, {"recursion_limit": 100}):  
        if "__end__" not in step:
            print("\nStep output:")
            print(step)
            print("\n" + "-" * 80 + "\n")

if __name__ == "__main__":
    main() 